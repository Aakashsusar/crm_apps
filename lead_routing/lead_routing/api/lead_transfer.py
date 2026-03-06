# Copyright (c) 2026, IP CRM and contributors
# For license information, please see license.txt

"""
Department-Based Lead Routing Engine.

Core logic for:
- Shift detection based on lead creation time
- Forward/backward/reject transitions between departments
- Assignment clearing and reassignment via Frappe Assignment Rules
- Department history logging
- Notifications
"""

import frappe
from frappe import _
from frappe.desk.form import assign_to
from frappe.utils import now_datetime, get_datetime, getdate


# ──────────────────────────────────────────────────────────────────────────────
# WHITELISTED API ENDPOINTS
# ──────────────────────────────────────────────────────────────────────────────


@frappe.whitelist()
def mark_department_done(lead_name):
	"""
	Current department marks its work as done.
	Lead moves to the next department in the pipeline.
	If current department is terminal, lead lifecycle ends.
	"""
	lead = frappe.get_doc("CRM Lead", lead_name, for_update=True, ignore_permissions=True)
	_validate_lead_has_department(lead)

	current_stage = frappe.get_doc("Department Pipeline Stage", lead.current_department)

	if current_stage.is_terminal:
		# Terminal stage — mark lead as complete
		lead.department_status = "Done"
		_close_current_log_entry(lead)
		lead.save(ignore_permissions=True)
		_add_comment(lead, "Completed", f"Lead lifecycle completed at {current_stage.stage_name}")
		_notify_department(lead, current_stage, "Completed")
		return {"status": "completed", "message": _("Lead lifecycle completed")}

	# Get the next stage
	next_stage = _get_next_stage(current_stage)
	if not next_stage:
		frappe.throw(_("No next stage configured after {0}").format(current_stage.stage_name))

	# Validate forward transition exists
	_validate_transition(current_stage.name, next_stage.name, "Forward")

	# Execute the transfer
	_execute_transfer(lead, next_stage, "Forward")

	return {
		"status": "transferred",
		"from": current_stage.stage_name,
		"to": next_stage.stage_name,
	}


@frappe.whitelist()
def send_back_to_department(lead_name):
	"""
	Send lead back to the previous department in the pipeline.
	"""
	lead = frappe.get_doc("CRM Lead", lead_name, for_update=True, ignore_permissions=True)
	_validate_lead_has_department(lead)

	current_stage = frappe.get_doc("Department Pipeline Stage", lead.current_department)

	target = _get_previous_stage(current_stage)
	if not target:
		frappe.throw(_("No previous stage configured before {0}").format(current_stage.stage_name))

	_execute_transfer(lead, target, "Backward")

	return {
		"status": "sent_back",
		"from": current_stage.stage_name,
		"to": target.stage_name,
	}


@frappe.whitelist()
def reject_to_onboarding(lead_name):
	"""
	Any department can reject a lead back to the first stage (Seller Onboarding).
	"""
	lead = frappe.get_doc("CRM Lead", lead_name, for_update=True, ignore_permissions=True)
	_validate_lead_has_department(lead)

	current_stage = frappe.get_doc("Department Pipeline Stage", lead.current_department)

	first_stage = _get_first_stage()
	if current_stage.name == first_stage.name:
		frappe.throw(_("Lead is already at the first stage"))

	# Check for reject transition rule
	_validate_transition(current_stage.name, first_stage.name, "Reject")

	lead.department_status = "Rejected"
	_execute_transfer(lead, first_stage, "Reject")

	return {
		"status": "rejected",
		"from": current_stage.stage_name,
		"to": first_stage.stage_name,
	}


@frappe.whitelist()
def manager_override_transfer(lead_name, target_stage, notes=""):
	"""
	Transfer a lead to any department.
	Allowed for department users, managers, and System Managers.
	"""
	lead = frappe.get_doc("CRM Lead", lead_name, for_update=True, ignore_permissions=True)
	_validate_lead_has_department(lead)

	current_stage = frappe.get_doc("Department Pipeline Stage", lead.current_department)

	target = frappe.get_doc("Department Pipeline Stage", target_stage)

	_execute_transfer(lead, target, "Manager Override", notes=notes)

	return {
		"status": "override_transferred",
		"from": current_stage.stage_name,
		"to": target.stage_name,
	}


@frappe.whitelist()
def get_transfer_targets(current_department):
	"""
	Returns a list of possible target departments for a lead,
	based on configured transition rules.
	"""
	current_stage_name = current_department

	# Get all enabled transition rules from the current stage
	transitions = frappe.get_all(
		"Department Transition Rule",
		filters={"from_stage": current_stage_name, "enabled": 1},
		fields=["to_stage", "transition_type"],
	)

	target_stages = []
	for t in transitions:
		target_stage_doc = frappe.get_doc("Department Pipeline Stage", t.to_stage)
		target_stages.append({
			"name": target_stage_doc.name,
			"stage_name": target_stage_doc.stage_name,
			"transition_type": t.transition_type,
		})

	# Add "Manager Override" option to all other enabled stages
	all_enabled_stages = frappe.get_all(
		"Department Pipeline Stage",
		filters={"enabled": 1},
		fields=["name", "stage_name"],
	)

	existing_target_names = {t["name"] for t in target_stages}
	for stage in all_enabled_stages:
		if stage.name != current_stage_name and stage.name not in existing_target_names:
			target_stages.append({
				"name": stage.name,
				"stage_name": stage.stage_name,
				"transition_type": "Manager Override",
			})

	# Sort by stage_name for consistent display
	target_stages.sort(key=lambda x: x["stage_name"])

	return target_stages


# ──────────────────────────────────────────────────────────────────────────────
# DOC EVENT HOOKS (called from hooks.py)
# ──────────────────────────────────────────────────────────────────────────────


def on_lead_created(doc, method=None):
	"""
	Hook: after_insert for CRM Lead.
	- If created by a department user, keep lead in their department
	  and assign it to the creator.
	- Otherwise, assign to the first pipeline stage (Seller Onboarding).

	IMPORTANT: Do NOT call doc.save() here. Calling save() inside after_insert
	creates a nested transaction that deadlocks on tabSeries (the naming series
	counter table). Use db.set_value() and direct child inserts instead.
	"""
	from lead_routing.api.crm_access import _is_department_user
	from frappe.desk.form import assign_to

	creator = frappe.session.user

	# Find the department of the creating user (if they're a dept member)
	creator_stage = None
	if creator and creator not in ("Administrator", "Guest") and _is_department_user(creator):
		user_roles = frappe.get_roles(creator)
		dept_stages = frappe.get_all(
			"Department Pipeline Stage",
			filters={"enabled": 1},
			fields=["name", "stage_name", "department_role", "manager_role"],
		)
		for stage in dept_stages:
			if stage.department_role and stage.department_role in user_roles:
				creator_stage = frappe.get_doc("Department Pipeline Stage", stage.name)
				break

	if creator_stage:
		# ── Department user created the lead → keep in their dept ──
		shift = _get_shift_for_time(doc.creation)

		# Use db.set_value to avoid nested transaction deadlock on tabSeries
		frappe.db.set_value("CRM Lead", doc.name, {
			"current_department": creator_stage.name,
			"current_shift": shift.name if shift else None,
			"department_status": "Working",
			"lead_owner": creator,
		}, update_modified=False)

		# Insert dept history child row directly
		frappe.get_doc({
			"doctype": "Lead Department Log",
			"parent": doc.name,
			"parenttype": "CRM Lead",
			"parentfield": "department_history",
			"department": creator_stage.name,
			"shift": shift.name if shift else None,
			"entered_at": now_datetime(),
			"action": "Initial",
			"assigned_user": creator,
		}).insert(ignore_permissions=True)
		frappe.db.commit()

		# Self-assign to creator
		_current_user = frappe.session.user or "Administrator"
		frappe.set_user("Administrator")
		try:
			assign_to.add({
				"doctype": "CRM Lead",
				"name": doc.name,
				"assign_to": [creator],
				"description": f"Self-assigned to {creator_stage.stage_name}",
				"notify": False,
			})
			frappe.share.add(
				"CRM Lead", doc.name, creator,
				read=1, write=1, share=1, notify=0
			)
		finally:
			frappe.set_user(_current_user)

		_add_comment(doc, "Initial Assignment",
			f"Lead created and self-assigned by {creator} in {creator_stage.stage_name}")

	else:
		# ── Admin/manager created the lead → normal pipeline routing ──
		first_stage = _get_first_stage()
		if not first_stage:
			return

		shift = _get_shift_for_time(doc.creation)

		# Use db.set_value to avoid nested transaction deadlock on tabSeries
		frappe.db.set_value("CRM Lead", doc.name, {
			"current_department": first_stage.name,
			"current_shift": shift.name if shift else None,
			"department_status": "Working",
		}, update_modified=False)

		# Insert dept history child row directly
		frappe.get_doc({
			"doctype": "Lead Department Log",
			"parent": doc.name,
			"parenttype": "CRM Lead",
			"parentfield": "department_history",
			"department": first_stage.name,
			"shift": shift.name if shift else None,
			"entered_at": now_datetime(),
			"action": "Initial",
		}).insert(ignore_permissions=True)
		frappe.db.commit()

		# Reload so _assign_to_least_loaded sees the fresh state
		doc.reload()
		_assign_to_least_loaded(doc, first_stage)

		_add_comment(doc, "Initial Assignment",
			f"Lead assigned to {first_stage.stage_name}" + (f" ({shift.shift_name})" if shift else ""))


def on_lead_validate(doc, method=None):
	"""
	Hook: validate for CRM Lead.
	Prevent direct manual changes to routing fields if they were changed outside of API.
	"""
	if doc.is_new():
		return

	# Skip validation if change is being made by the routing system
	if doc.flags.get("via_lead_routing"):
		return

	# Check if routing fields were changed manually
	if doc.has_value_changed("current_department"):
		old_dept = doc.get_doc_before_save()
		if old_dept and old_dept.current_department:
			frappe.throw(
				_("Department changes must be made through the routing system buttons. "
				  "Direct edits are not allowed.")
			)


# ──────────────────────────────────────────────────────────────────────────────
# INTERNAL HELPER FUNCTIONS
# ──────────────────────────────────────────────────────────────────────────────


def _execute_transfer(lead, target_stage, action, notes=""):
	"""
	Core transfer logic:
	1. Close current department log entry
	2. Clear existing Frappe assignments
	3. Update current_department on the lead
	4. Set department_status = Working
	5. Create new department log entry
	6. Save lead → triggers Assignment Rule
	7. Send notifications
	"""
	old_department = lead.current_department

	# 1. Close current log entry
	_close_current_log_entry(lead)

	# 2. Clear existing assignments
	try:
		assign_to.clear("CRM Lead", lead.name, ignore_permissions=True)
	except Exception:
		pass

	# 3 & 4. Update routing fields
	lead.flags.via_lead_routing = True
	lead.current_department = target_stage.name
	lead.department_status = "Working"

	# 5. Create new department log entry
	lead.append("department_history", {
		"department": target_stage.name,
		"shift": lead.current_shift,
		"entered_at": now_datetime(),
		"action": action,
		"notes": notes,
	})

	# 6. Save — this triggers Assignment Rules
	lead.save(ignore_permissions=True)

	# Auto-assign to least loaded team member in target department
	_assign_to_least_loaded(lead, target_stage)

	# 7. Add timeline comment
	action_labels = {
		"Forward": "moved forward to",
		"Backward": "sent back to",
		"Reject": "rejected back to",
		"Manager Override": "manually transferred to",
	}
	label = action_labels.get(action, "transferred to")
	_add_comment(lead, action,
		f"Lead {label} {target_stage.stage_name}" + (f" — {notes}" if notes else ""))

	# 8. Notify
	_notify_department(lead, target_stage, action)


def _validate_lead_has_department(lead):
	"""Ensure lead has a current department assigned."""
	if not lead.current_department:
		frappe.throw(_("This lead has not been assigned to any department yet"))





def _validate_transition(from_stage, to_stage, transition_type):
	"""Check if a transition is allowed per Department Transition Rule."""
	exists = frappe.db.exists(
		"Department Transition Rule",
		{
			"from_stage": from_stage,
			"to_stage": to_stage,
			"transition_type": transition_type,
			"enabled": 1,
		},
	)
	if not exists:
		frappe.throw(
			_("Transition from {0} to {1} ({2}) is not allowed").format(
				from_stage, to_stage, transition_type
			)
		)


def _get_next_stage(current_stage):
	"""Get the next enabled stage by stage_order."""
	next_stages = frappe.get_all(
		"Department Pipeline Stage",
		filters={
			"stage_order": (">", current_stage.stage_order),
			"enabled": 1,
		},
		fields=["name", "stage_name", "stage_order", "is_terminal"],
		order_by="stage_order ASC",
		limit=1,
	)
	if next_stages:
		return frappe.get_doc("Department Pipeline Stage", next_stages[0].name)
	return None


def _get_previous_stage(current_stage):
	"""Get the previous enabled stage by stage_order."""
	prev_stages = frappe.get_all(
		"Department Pipeline Stage",
		filters={
			"stage_order": ("<", current_stage.stage_order),
			"enabled": 1,
		},
		fields=["name", "stage_name", "stage_order", "is_terminal"],
		order_by="stage_order DESC",
		limit=1,
	)
	if prev_stages:
		return frappe.get_doc("Department Pipeline Stage", prev_stages[0].name)
	return None


def _get_first_stage():
	"""Get the first enabled stage (lowest stage_order)."""
	stages = frappe.get_all(
		"Department Pipeline Stage",
		filters={"enabled": 1},
		fields=["name"],
		order_by="stage_order ASC",
		limit=1,
	)
	if stages:
		return frappe.get_doc("Department Pipeline Stage", stages[0].name)
	return None


def _get_shift_for_time(dt):
	"""
	Determine which shift a datetime falls into.
	Supports overnight shifts (where end_time < start_time).
	Falls back to the nearest shift if no exact match.
	"""
	from datetime import timedelta

	if not dt:
		dt = now_datetime()

	dt = get_datetime(dt)
	time_val = dt.time()

	shifts = frappe.get_all(
		"Department Shift",
		filters={"enabled": 1},
		fields=["name", "shift_name", "start_time", "end_time"],
		order_by="start_time ASC",
	)

	if not shifts:
		return None

	for shift in shifts:
		start = _to_time(shift.start_time)
		end = _to_time(shift.end_time)

		if start <= end:
			# Normal shift (e.g., 06:00 - 14:00)
			if start <= time_val < end:
				return frappe._dict(shift)
		else:
			# Overnight shift (e.g., 22:00 - 06:00)
			if time_val >= start or time_val < end:
				return frappe._dict(shift)

	# No exact match — return the first shift as fallback
	return frappe._dict(shifts[0])


def _to_time(val):
	"""Convert a timedelta or time value to a time object."""
	from datetime import timedelta, time

	if isinstance(val, timedelta):
		total_seconds = int(val.total_seconds())
		hours = total_seconds // 3600
		minutes = (total_seconds % 3600) // 60
		seconds = total_seconds % 60
		return time(hours, minutes, seconds)
	if isinstance(val, time):
		return val
	# String fallback
	if isinstance(val, str):
		parts = val.split(":")
		return time(int(parts[0]), int(parts[1]), int(parts[2]) if len(parts) > 2 else 0)
	return val


def _close_current_log_entry(lead):
	"""Close the most recent open department log entry."""
	if not lead.department_history:
		return

	for entry in reversed(lead.department_history):
		if not entry.exited_at:
			entry.exited_at = now_datetime()
			# Only fill assigned_user if it's still empty (it may have been
			# set earlier by _assign_to_least_loaded or on_lead_created)
			if not entry.assigned_user:
				assigned_users = list(lead.get_assigned_users()) if hasattr(lead, "get_assigned_users") else []
				if assigned_users:
					entry.assigned_user = assigned_users[0]
			break


def _assign_to_least_loaded(lead, stage):
	"""
	Assign the lead to the team member in this department with the least
	open CRM Lead assignments (load balancing).
	Filters team members by the lead's current_shift when available.
	"""
	if not stage.team_members:
		frappe.log_error(
			message=f"No team members configured for {stage.stage_name}",
			title=f"Lead Routing: No Team Members",
		)
		return

	# Get active team members
	all_active_members = [m for m in stage.team_members if m.is_active]
	if not all_active_members:
		frappe.log_error(
			message=f"No active team members in {stage.stage_name}",
			title=f"Lead Routing: No Active Members",
		)
		return

	# Filter by shift: strict shift isolation
	# Priority: 1) exact shift match, 2) members with no shift set, 3) all active
	lead_shift = getattr(lead, "current_shift", None)
	if lead_shift:
		# First try: only members explicitly assigned to this shift
		exact_shift_members = [
			m.user for m in all_active_members
			if m.shift == lead_shift
		]
		if exact_shift_members:
			active_members = exact_shift_members
		else:
			# Fallback: members with no shift set (unassigned to any shift)
			no_shift_members = [
				m.user for m in all_active_members
				if not m.shift
			]
			active_members = no_shift_members if no_shift_members else [m.user for m in all_active_members]
	else:
		active_members = [m.user for m in all_active_members]

	# Count open CRM Lead assignments per team member
	assignments = frappe.get_all(
		"ToDo",
		filters={
			"reference_type": "CRM Lead",
			"allocated_to": ("in", active_members),
			"status": "Open",
		},
		fields=["allocated_to", "count(name) as cnt"],
		group_by="allocated_to",
	)

	# Build a count map (default 0 for members with no assignments)
	count_map = {m: 0 for m in active_members}
	for a in assignments:
		if a.allocated_to in count_map:
			count_map[a.allocated_to] = a.cnt

	# Pick the user with the fewest open assignments
	least_loaded_user = min(count_map, key=count_map.get)

	# Clear any existing assignments and standard shares first
	try:
		# Remove old shares before reassigning (except for owners/creators)
		old_assignees = [d.user for d in frappe.db.get_all("DocShare", filters={"share_doctype": "CRM Lead", "share_name": lead.name}, fields=["user"])]
		
		assign_to.clear("CRM Lead", lead.name, ignore_permissions=True)
		
		# Replace full removal with read-only permission for old assignees
		for old_user in old_assignees:
			frappe.share.add(
				"CRM Lead",
				lead.name,
				old_user,
				read=1,
				write=0,
				share=0,
				notify=0
			)
	except Exception:
		pass

	# Assign to the least loaded user
	# Run as Administrator to bypass share permission checks
	current_user = frappe.session.user or "Administrator"
	frappe.set_user("Administrator")
	try:
		assign_to.add({
			"doctype": "CRM Lead",
			"name": lead.name,
			"assign_to": [least_loaded_user],
			"description": f"Auto-assigned by Lead Routing (Department: {stage.stage_name})",
			"notify": False,
		})
		
		# Explicitly grant DocShare permissions so the new owner can actually edit/route it
		frappe.share.add(
			"CRM Lead",
			lead.name,
			least_loaded_user,
			read=1,
			write=1,
			share=1,
			notify=1
		)
	finally:
		frappe.set_user(current_user)

	# Also set lead_owner so the CRM dashboard metrics work correctly
	frappe.db.set_value("CRM Lead", lead.name, "lead_owner", least_loaded_user, update_modified=False)

	# Update the latest department log entry with the assigned user
	latest_log = frappe.get_all(
		"Lead Department Log",
		filters={
			"parent": lead.name,
			"parenttype": "CRM Lead",
			"department": stage.name,
		},
		fields=["name"],
		order_by="creation desc",
		limit=1,
	)
	if latest_log:
		frappe.db.set_value(
			"Lead Department Log", latest_log[0].name,
			"assigned_user", least_loaded_user,
			update_modified=False,
		)

	frappe.msgprint(
		f"Lead assigned to {frappe.utils.get_fullname(least_loaded_user)} ({stage.stage_name})",
		alert=True,
	)


def _add_comment(lead, action, content):
	"""Add a comment to the lead's timeline."""
	frappe.get_doc({
		"doctype": "Comment",
		"comment_type": "Info",
		"reference_doctype": "CRM Lead",
		"reference_name": lead.name,
		"content": f"<strong>🔄 Lead Routing — {action}:</strong> {content}",
	}).insert(ignore_permissions=True)


def _notify_department(lead, stage, action):
	"""
	Send notification to department manager and assigned user.
	Uses Frappe's built-in notification system.
	"""
	recipients = set()

	# Notify department manager(s)
	if stage.manager_role:
		managers = frappe.get_all(
			"Has Role",
			filters={"role": stage.manager_role, "parenttype": "User"},
			fields=["parent"],
		)
		for m in managers:
			user = m.parent
			if user and frappe.db.get_value("User", user, "enabled"):
				recipients.add(user)

	# Notify currently assigned user
	if hasattr(lead, "get_assigned_users"):
		for user in lead.get_assigned_users():
			recipients.add(user)

	# Send system notifications
	for recipient in recipients:
		try:
			frappe.publish_realtime(
				"lead_routing_update",
				{
					"lead": lead.name,
					"lead_name": lead.lead_name,
					"department": stage.stage_name,
					"action": action,
				},
				user=recipient,
			)
		except Exception:
			pass

	# Create Frappe notification log
	action_messages = {
		"Forward": f"Lead {lead.lead_name} has been forwarded to {stage.stage_name}",
		"Backward": f"Lead {lead.lead_name} has been sent back to {stage.stage_name}",
		"Reject": f"Lead {lead.lead_name} has been rejected back to {stage.stage_name}",
		"Manager Override": f"Lead {lead.lead_name} was manually transferred to {stage.stage_name}",
		"Initial Assignment": f"New lead {lead.lead_name} assigned to {stage.stage_name}",
		"Completed": f"Lead {lead.lead_name} lifecycle completed at {stage.stage_name}",
	}

	message = action_messages.get(action, f"Lead {lead.lead_name} routed to {stage.stage_name}")

	for recipient in recipients:
		try:
			notification = frappe.new_doc("Notification Log")
			notification.for_user = recipient
			notification.from_user = frappe.session.user
			notification.document_type = "CRM Lead"
			notification.document_name = lead.name
			notification.subject = message
			notification.type = "Alert"
			notification.insert(ignore_permissions=True)
		except Exception:
			pass


# ──────────────────────────────────────────────────────────────────────────────
# UTILITY FUNCTIONS (exported for use in permissions, etc.)
# ──────────────────────────────────────────────────────────────────────────────


def get_user_department_stages():
	"""
	Get all Department Pipeline Stages where the current user has a role.
	Returns a list of stage names.
	"""
	user_roles = frappe.get_roles()

	if "System Manager" in user_roles or "Administrator" in user_roles:
		return frappe.get_all(
			"Department Pipeline Stage",
			filters={"enabled": 1},
			pluck="name",
		)

	stages = frappe.get_all(
		"Department Pipeline Stage",
		filters={"enabled": 1},
		fields=["name", "department_role", "manager_role"],
	)

	user_stages = []
	for stage in stages:
		if stage.department_role in user_roles or stage.manager_role in user_roles:
			user_stages.append(stage.name)

	return user_stages


@frappe.whitelist()
def get_user_department_stages():
	"""Get all stages where user is a team member or a manager."""
	user_roles = frappe.get_roles()

	if "System Manager" in user_roles or "Administrator" in user_roles:
		return frappe.get_all(
			"Department Pipeline Stage",
			filters={"enabled": 1},
			pluck="name",
		)

	stages = frappe.get_all(
		"Department Pipeline Stage",
		filters={"enabled": 1},
		fields=["name", "department_role", "manager_role"],
	)

	user_stages = []
	for stage in stages:
		if (stage.department_role and stage.department_role in user_roles) or \
		   (stage.manager_role and stage.manager_role in user_roles):
			user_stages.append(stage.name)

	return user_stages


@frappe.whitelist()
def get_user_managed_stages():
	"""Get stages where user is a manager."""
	user_roles = frappe.get_roles()

	if "System Manager" in user_roles or "Administrator" in user_roles:
		return frappe.get_all(
			"Department Pipeline Stage",
			filters={"enabled": 1},
			pluck="name",
		)

	stages = frappe.get_all(
		"Department Pipeline Stage",
		filters={"enabled": 1},
		fields=["name", "manager_role"],
	)

	return [s.name for s in stages if s.manager_role in user_roles]


def get_lead_department_history(lead_name):
	"""Get the full department history for a lead (for API access)."""
	lead = frappe.get_doc("CRM Lead", lead_name)
	return [
		{
			"department": h.department,
			"shift": h.shift,
			"assigned_user": h.assigned_user,
			"entered_at": h.entered_at,
			"exited_at": h.exited_at,
			"action": h.action,
			"notes": h.notes,
		}
		for h in lead.department_history
	]

