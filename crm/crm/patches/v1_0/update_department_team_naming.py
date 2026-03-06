"""
Migration script to update existing Department and Team names
to support same department names across different shifts
"""
import frappe


def execute():
	"""Update naming for departments and teams"""
	
	frappe.logger().info("Starting department and team naming migration...")
	
	# Update existing departments
	update_departments()
	
	# Update existing teams
	update_teams()
	
	frappe.db.commit()
	frappe.logger().info("Department and team naming migration completed!")


def update_departments():
	"""Update department names to include shift code"""
	
	departments = frappe.get_all(
		"CRM Department",
		fields=["name", "department_name", "shift"]
	)
	
	for dept in departments:
		if not dept.shift:
			continue
		
		try:
			shift_doc = frappe.get_doc("CRM Shift", dept.shift)
			shift_code = shift_doc.shift_code or shift_doc.shift_name
			new_name = f"{shift_code}-{dept.department_name}"
			
			# Skip if already in correct format
			if dept.name == new_name:
				continue
			
			# Check if new name already exists
			if frappe.db.exists("CRM Department", new_name):
				frappe.logger().warning(f"Department {new_name} already exists, skipping {dept.name}")
				continue
			
			# Rename the department
			frappe.rename_doc("CRM Department", dept.name, new_name, force=True)
			frappe.logger().info(f"Renamed department: {dept.name} → {new_name}")
			
		except Exception as e:
			frappe.logger().error(f"Error updating department {dept.name}: {str(e)}")
			continue


def update_teams():
	"""Update team names to include department"""
	
	teams = frappe.get_all(
		"CRM Team",
		fields=["name", "team_name", "department"]
	)
	
	for team in teams:
		if not team.department:
			continue
		
		try:
			new_name = f"{team.department}-{team.team_name}"
			
			# Skip if already in correct format
			if team.name == new_name:
				continue
			
			# Check if new name already exists
			if frappe.db.exists("CRM Team", new_name):
				frappe.logger().warning(f"Team {new_name} already exists, skipping {team.name}")
				continue
			
			# Rename the team
			frappe.rename_doc("CRM Team", team.name, new_name, force=True)
			frappe.logger().info(f"Renamed team: {team.name} → {new_name}")
			
		except Exception as e:
			frappe.logger().error(f"Error updating team {team.name}: {str(e)}")
			continue
