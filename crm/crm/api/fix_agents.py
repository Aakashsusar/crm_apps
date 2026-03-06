"""
Quick API to check and assign agents to teams
"""
import frappe
from frappe import _


@frappe.whitelist()
def check_team_agents(team_name):
	"""Check which agents are assigned to a team"""
	
	if not frappe.db.exists("CRM Team", team_name):
		return {"error": f"Team '{team_name}' not found"}
	
	team = frappe.get_doc("CRM Team", team_name)
	
	# Get team members from CRM Team Member
	team_members = frappe.get_all(
		"CRM Team Member",
		filters={"team": team_name},
		fields=["user", "user_name", "role"]
	)
	
	# Get full user details
	agents = []
	for member in team_members:
		user = frappe.db.get_value(
			"User",
			member.user,
			["name", "full_name", "email", "enabled"],
			as_dict=True
		)
		if user:
			agents.append({
				"name": user.name,
				"full_name": user.full_name,
				"email": user.email,
				"enabled": user.enabled,
				"role": member.role
			})
	
	return {
		"team": {
			"name": team.name,
			"team_name": team.team_name,
			"department": team.department,
			"shift": team.shift
		},
		"agents": agents,
		"agent_count": len(agents)
	}


@frappe.whitelist()
def assign_user_to_team(user_email, team_name):
	"""Assign a user to a team"""
	
	if not frappe.db.exists("User", user_email):
		frappe.throw(f"User '{user_email}' not found")
	
	if not frappe.db.exists("CRM Team", team_name):
		frappe.throw(f"Team '{team_name}' not found")
	
	# Update user
	frappe.db.set_value("User", user_email, "crm_team", team_name)
	frappe.db.commit()
	
	# Get updated user info
	user = frappe.get_doc("User", user_email)
	
	return {
		"success": True,
		"user": user_email,
		"full_name": user.full_name,
		"team": user.crm_team,
		"department": user.crm_department,
		"shift": user.crm_shift
	}


@frappe.whitelist()
def list_all_teams_with_agents():
	"""List all teams and their agents"""
	
	teams = frappe.get_all(
		"CRM Team",
		fields=["name", "team_name", "department", "shift"],
		order_by="name"
	)
	
	result = []
	
	for team in teams:
		# Get team members from CRM Team Member
		team_members = frappe.get_all(
			"CRM Team Member",
			filters={"team": team.name},
			fields=["user", "user_name", "role"]
		)
		
		# Get full user details
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
		
		result.append({
			"team_name": team.team_name,
			"team_id": team.name,
			"department": team.department,
			"shift": team.shift,
			"agent_count": len(agents),
			"agents": agents
		})
	
	return result


@frappe.whitelist()
def get_users_without_team():
	"""Get all users who are not assigned to any team"""
	
	users = frappe.get_all(
		"User",
		filters={
			"enabled": 1,
			"user_type": "System User",
			"name": ["not in", ["Administrator", "Guest"]]
		},
		fields=["name", "full_name", "email", "crm_team"],
		order_by="full_name"
	)
	
	# Filter users without team
	users_without_team = [u for u in users if not u.get("crm_team")]
	
	return {
		"total_users": len(users),
		"users_without_team": len(users_without_team),
		"users": users_without_team
	}
