"""
API endpoints for CRM Hierarchy Management
Shift → Department → Team → Agent
"""
import frappe
from frappe import _


@frappe.whitelist()
def get_user_hierarchy():
	"""Get current user's hierarchy information"""
	user = frappe.session.user
	
	user_doc = frappe.get_doc("User", user)
	
	team = user_doc.get("crm_team")
	department = user_doc.get("crm_department")
	shift = user_doc.get("crm_shift")
	
	result = {
		"user": user,
		"full_name": user_doc.full_name,
		"team": None,
		"department": None,
		"shift": None,
		"is_shift_active": False,
		"remaining_minutes": 0
	}
	
	if team:
		team_doc = frappe.get_doc("CRM Team", team)
		result["team"] = {
			"name": team_doc.name,
			"team_name": team_doc.team_name,
			"team_leader": team_doc.team_leader
		}
	
	if department:
		dept_doc = frappe.get_doc("CRM Department", department)
		result["department"] = {
			"name": dept_doc.name,
			"department_name": dept_doc.department_name,
			"department_head": dept_doc.department_head
		}
	
	if shift:
		shift_doc = frappe.get_doc("CRM Shift", shift)
		is_active = shift_doc.is_active_now()
		result["shift"] = {
			"name": shift_doc.name,
			"shift_name": shift_doc.shift_name,
			"start_time": str(shift_doc.start_time),
			"end_time": str(shift_doc.end_time)
		}
		result["is_shift_active"] = is_active
		result["remaining_minutes"] = shift_doc.get_remaining_time() if is_active else 0
	
	return result


@frappe.whitelist()
def get_hierarchy_tree():
	"""Get complete hierarchy tree: Shifts → Departments → Teams → Agents"""
	
	current_user = frappe.session.user
	user_roles = frappe.get_roles(current_user)
	
	# Check if user is Administrator, System Manager, or Sales Manager (full access)
	is_admin = (
		current_user == "Administrator" or 
		"Administrator" in user_roles or 
		"System Manager" in user_roles or
		"Sales Manager" in user_roles
	)
	
	# Check if user is Sales User (restricted access)
	# IMPORTANT: Only restrict if user is Sales User AND NOT an admin
	is_sales_user = "Sales User" in user_roles and not is_admin
	
	# Debug logging
	frappe.logger().info(f"[HIERARCHY] User: {current_user}, Roles: {user_roles}")
	frappe.logger().info(f"[HIERARCHY] is_admin: {is_admin}, is_sales_user: {is_sales_user}")
	
	shifts = frappe.get_all(
		"CRM Shift",
		filters={"enabled": 1},
		fields=["name", "shift_name", "start_time", "end_time"],
		order_by="start_time"
	)
	
	frappe.logger().info(f"[HIERARCHY] Total shifts in database: {len(shifts)}")
	
	tree = []
	
	# If Sales User (NOT admin), get user's team to filter
	user_team = None
	user_department = None
	user_shift = None
	
	if is_sales_user:
		# Check if user is a team member
		team_member = frappe.db.get_value(
			"CRM Team Member",
			{"user": current_user},
			["team", "name"],
			as_dict=True
		)
		
		if team_member:
			user_team = team_member.team
			# Get team details to find department and shift
			team_doc = frappe.get_doc("CRM Team", user_team)
			user_department = team_doc.department
			user_shift = team_doc.shift
			
			frappe.logger().info(f"[HIERARCHY] Sales User {current_user} - Team: {user_team}, Dept: {user_department}, Shift: {user_shift}")
	
	for shift in shifts:
		# IMPORTANT: Only filter if user is Sales User (not admin)
		if is_sales_user and user_shift and shift.name != user_shift:
			frappe.logger().info(f"[HIERARCHY] Skipping shift {shift.name} for Sales User")
			continue
		
		frappe.logger().info(f"[HIERARCHY] Processing shift: {shift.shift_name} ({shift.name})")
		
		shift_node = {
			"name": shift.name,
			"shift_name": shift.shift_name,
			"start_time": str(shift.start_time),
			"end_time": str(shift.end_time),
			"departments": []
		}
		
		# Get departments for this shift
		departments = frappe.get_all(
			"CRM Department",
			filters={"shift": shift.name, "enabled": 1},
			fields=["name", "department_name", "department_head"]
		)
		
		frappe.logger().info(f"[HIERARCHY] Found {len(departments)} departments for shift {shift.shift_name}")
		
		for dept in departments:
			# IMPORTANT: Only filter if user is Sales User (not admin)
			if is_sales_user and user_department and dept.name != user_department:
				frappe.logger().info(f"[HIERARCHY] Skipping department {dept.name} for Sales User")
				continue
			
			frappe.logger().info(f"[HIERARCHY] Processing department: {dept.department_name} ({dept.name})")
			
			dept_node = {
				"name": dept.name,
				"department_name": dept.department_name,
				"department_head": dept.department_head,
				"teams": []
			}
			
			# Get teams for this department
			teams = frappe.get_all(
				"CRM Team",
				filters={"department": dept.name, "enabled": 1},
				fields=["name", "team_name", "team_leader"]
			)
			
			frappe.logger().info(f"[HIERARCHY] Found {len(teams)} teams for department {dept.department_name}")
			
			for team in teams:
				# IMPORTANT: Only filter if user is Sales User (not admin)
				if is_sales_user and user_team and team.name != user_team:
					frappe.logger().info(f"[HIERARCHY] Skipping team {team.name} for Sales User")
					continue
				
				team_node = {
					"name": team.name,
					"team_name": team.team_name,
					"team_leader": team.team_leader,
					"agents": []
				}
				
				# Get agents for this team from CRM Team Member
				team_members = frappe.get_all(
					"CRM Team Member",
					filters={"team": team.name},
					fields=["user", "user_name", "role"]
				)
				
				# Get full user details for each team member
				agents = []
				for member in team_members:
					user = frappe.db.get_value(
						"User",
						member.user,
						["name", "full_name", "email", "enabled"],
						as_dict=True
					)
					if user and user.enabled:
						agents.append({
							"name": user.name,
							"full_name": user.full_name,
							"email": user.email,
							"role": member.role
						})
				
				# Debug logging
				frappe.logger().debug(f"Team {team.name} ({team.team_name}): Found {len(agents)} agents")
				for agent in agents:
					frappe.logger().debug(f"  - Agent: {agent['full_name']} ({agent['name']}) - Role: {agent.get('role', 'N/A')}")
				
				team_node["agents"] = agents
				dept_node["teams"].append(team_node)
			
			# Add department to shift
			# For admins: add all departments (even if no teams)
			# For sales users: only add if has teams
			if is_admin or dept_node["teams"]:
				shift_node["departments"].append(dept_node)
				frappe.logger().info(f"[HIERARCHY] Added department {dept.department_name} with {len(dept_node['teams'])} teams")
			else:
				frappe.logger().info(f"[HIERARCHY] Skipped empty department {dept.department_name}")
		
		# Add shift to tree
		# For admins: add all shifts (even if no departments)
		# For sales users: only add if has departments
		if is_admin or shift_node["departments"]:
			tree.append(shift_node)
			frappe.logger().info(f"[HIERARCHY] Added shift {shift.shift_name} with {len(shift_node['departments'])} departments")
		else:
			frappe.logger().info(f"[HIERARCHY] Skipped empty shift {shift.shift_name}")
	
	# Log access level and results
	frappe.logger().info(f"[HIERARCHY] Returning {len(tree)} shifts to user")
	if is_admin:
		frappe.logger().info(f"[HIERARCHY] Administrator/System Manager/Sales Manager {current_user} - Full access to all hierarchy")
	elif is_sales_user:
		frappe.logger().info(f"[HIERARCHY] Sales User {current_user} - Filtered access: Shift={user_shift}, Dept={user_department}, Team={user_team}")
	else:
		frappe.logger().info(f"[HIERARCHY] User {current_user} with roles {user_roles} - Full access (no Sales User role)")
	
	return tree


@frappe.whitelist()
def validate_shift_access():
	"""Validate if current user can access auto dialer based on shift timing"""
	hierarchy = get_user_hierarchy()
	
	if not hierarchy.get("shift"):
		return {
			"allowed": False,
			"message": "You are not assigned to any shift"
		}
	
	if not hierarchy.get("is_shift_active"):
		shift = hierarchy["shift"]
		return {
			"allowed": False,
			"message": f"Your shift ({shift['shift_name']}) is not active now. Shift timing: {shift['start_time']} - {shift['end_time']}"
		}
	
	remaining = hierarchy.get("remaining_minutes", 0)
	
	if remaining < 30:
		return {
			"allowed": True,
			"warning": f"Your shift ends in {remaining} minutes. Auto dialer may be paused automatically.",
			"remaining_minutes": remaining
		}
	
	return {
		"allowed": True,
		"message": "You can start auto dialer",
		"remaining_minutes": remaining
	}


@frappe.whitelist()
def get_my_leads_for_dialer():
	"""Get leads for current user based on hierarchy (for auto dialer)"""
	user = frappe.session.user
	hierarchy = get_user_hierarchy()
	
	# Validate shift access
	access = validate_shift_access()
	if not access.get("allowed"):
		frappe.throw(access.get("message"))
	
	filters = {
		"mobile_no": ["!=", ""],
		"status": ["in", ["Lead", "Open", "Contacted"]]
	}
	
	# Filter by hierarchy
	team = hierarchy.get("team", {}).get("name")
	department = hierarchy.get("department", {}).get("name")
	shift = hierarchy.get("shift", {}).get("name")
	
	# Priority: Own leads > Team leads > Department leads
	or_filters = [
		{"lead_owner": user}
	]
	
	if team:
		or_filters.append({"assigned_team": team})
	
	if department:
		or_filters.append({"assigned_department": department})
	
	# Get leads
	leads = frappe.get_all(
		"CRM Lead",
		filters=filters,
		or_filters=or_filters,
		fields=["name", "lead_name", "mobile_no", "status", "lead_owner", "assigned_team", "assigned_shift"],
		limit=100,
		order_by="creation desc"
	)
	
	return {
		"leads": leads,
		"count": len(leads),
		"hierarchy": hierarchy,
		"access": access
	}


@frappe.whitelist()
def assign_lead_to_hierarchy(lead, team=None, department=None):
	"""Assign a lead to team/department (auto-fills shift)"""
	if not lead:
		frappe.throw("Lead is required")
	
	lead_doc = frappe.get_doc("CRM Lead", lead)
	
	if team:
		team_doc = frappe.get_doc("CRM Team", team)
		lead_doc.assigned_team = team
		lead_doc.assigned_department = team_doc.department
		lead_doc.assigned_shift = team_doc.shift
	elif department:
		dept_doc = frappe.get_doc("CRM Department", department)
		lead_doc.assigned_department = department
		lead_doc.assigned_shift = dept_doc.shift
	
	lead_doc.save(ignore_permissions=True)
	
	return {
		"success": True,
		"lead": lead,
		"assigned_team": lead_doc.assigned_team,
		"assigned_department": lead_doc.assigned_department,
		"assigned_shift": lead_doc.assigned_shift
	}
