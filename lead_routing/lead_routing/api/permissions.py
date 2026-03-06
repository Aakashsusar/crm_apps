# Copyright (c) 2026, IP CRM and contributors
# For license information, please see license.txt

"""
Permission controls for department-based lead access.

- Regular department users: only see leads ASSIGNED to them (via ToDo)
- Department managers: see all leads in their department
- System Manager / Administrator: full access
"""

import frappe


def get_permission_query(user=None):
	"""
	Permission query condition for CRM Lead list views.
	Returns SQL WHERE clause to filter leads visible to the user.
	"""
	if not user:
		user = frappe.session.user

	if user == "Administrator":
		return ""

	user_roles = frappe.get_roles(user)

	if "System Manager" in user_roles:
		return ""

	# Get departments where user has a role
	stages = frappe.get_all(
		"Department Pipeline Stage",
		filters={"enabled": 1},
		fields=["name", "department_role", "manager_role"],
	)

	manager_stages = []
	user_stages = []

	for stage in stages:
		if stage.manager_role and stage.manager_role in user_roles:
			manager_stages.append(stage.name)
		elif stage.department_role and stage.department_role in user_roles:
			user_stages.append(stage.name)

	if not manager_stages and not user_stages:
		# No department role — fall back to default Frappe permissions
		return ""

	conditions = []
	escaped_user = frappe.db.escape(user)

	# Managers: see ALL leads in their department(s)
	if manager_stages:
		stage_list = ", ".join(frappe.db.escape(s) for s in manager_stages)
		conditions.append(f"`tabCRM Lead`.`current_department` IN ({stage_list})")

	# Regular users: see ONLY leads assigned to them (via ToDo)
	if user_stages:
		conditions.append(
			f"`tabCRM Lead`.`name` IN ("
			f"  SELECT `reference_name` FROM `tabToDo`"
			f"  WHERE `allocated_to` = {escaped_user}"
			f"  AND `reference_type` = 'CRM Lead'"
			f"  AND `status` = 'Open'"
			f")"
		)

	return "(" + " OR ".join(conditions) + ")"


def has_permission(doc, ptype=None, user=None):
	"""
	Fine-grained permission check for individual CRM Lead documents.
	"""
	if not user:
		user = frappe.session.user

	if user == "Administrator":
		return True

	user_roles = frappe.get_roles(user)

	if "System Manager" in user_roles:
		return True

	# If no department is set, fall back to default permissions
	if not doc.get("current_department"):
		return True

	current_dept = doc.get("current_department")

	# Check if user is a manager of the current department
	stage = frappe.get_cached_doc("Department Pipeline Stage", current_dept)

	if stage.manager_role and stage.manager_role in user_roles:
		return True  # Managers see all leads in their department

	# Regular department user: check if lead is assigned to them
	if stage.department_role and stage.department_role in user_roles:
		assigned = frappe.db.exists("ToDo", {
			"allocated_to": user,
			"reference_type": "CRM Lead",
			"reference_name": doc.name,
			"status": "Open",
		})
		if assigned:
			return True

	# Check if user handled this lead in the past (read-only access to their history)
	if ptype in ("read", "report", "email", "print"):
		if frappe.db.exists(
			"Lead Department Log",
			{
				"parent": doc.name,
				"parenttype": "CRM Lead",
				"assigned_user": user,
			},
		):
			return True

	return False
