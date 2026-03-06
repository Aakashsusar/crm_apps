import frappe
from frappe import _


@frappe.whitelist()
def get_user_departments():
	"""
	Get departments accessible by the current user with hierarchical team and user data.
	Only returns departments where user is a team member.
	"""
	user = frappe.session.user
	
	# System Managers and Administrators can see all departments
	if "System Manager" in frappe.get_roles(user) or user == "Administrator":
		departments = frappe.get_all(
			"CRM Department",
			filters={"enabled": 1},
			fields=["name", "department_name", "description"]
		)
		# Add ALL teams and member data to each department
		for dept in departments:
			dept["teams"] = get_department_teams(dept["name"])
		return departments
	
	# Get teams where user is a member
	team_members = frappe.get_all(
		"CRM Team Member",
		filters={"user": user},
		fields=["team"],
		pluck="team"
	)
	
	if not team_members:
		return []
	
	# Get teams
	teams = frappe.get_all(
		"CRM Team",
		filters={
			"name": ["in", team_members],
			"enabled": 1
		},
		fields=["name", "department"]
	)
	
	if not teams:
		return []
	
	# Get unique departments
	department_names = list(set([team.department for team in teams]))
	
	departments = frappe.get_all(
		"CRM Department",
		filters={
			"name": ["in", department_names],
			"enabled": 1
		},
		fields=["name", "department_name", "description"]
	)
	
	# Add team and member data to each department (only teams user belongs to)
	for dept in departments:
		user_teams = [t.name for t in teams if t.department == dept["name"]]
		dept["teams"] = get_department_teams(dept["name"], user_teams)
	
	return departments


def get_department_teams(department, team_filter=None):
	"""
	Get teams for a department with member count and lead count.
	"""
	filters = {"department": department, "enabled": 1}
	if team_filter:
		filters["name"] = ["in", team_filter]
	
	teams = frappe.get_all(
		"CRM Team",
		filters=filters,
		fields=["name", "team_name", "description"]
	)

	for team in teams:
		# Get team members
		members = frappe.get_all(
			"CRM Team Member",
			filters={"team": team.name},
			fields=["user", "user_name", "role"]
		)

		team["members"] = members
		team["member_count"] = len(members)
		
		# Get lead count for each team member
		for member in members:
			lead_count = frappe.db.count("CRM Lead", {"lead_owner": member.user})
			member["lead_count"] = lead_count
		
		# Total leads for the team
		team["total_leads"] = sum([m.get("lead_count", 0) for m in members])
	
	return teams


@frappe.whitelist()
def get_department_slug(department_name):
	"""Get URL-friendly slug for department"""
	return frappe.scrub(department_name)
