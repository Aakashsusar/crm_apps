import frappe
from frappe.model.document import Document


class CRMTeam(Document):
	"""CRM Team"""
	
	def autoname(self):
		"""Auto-generate name as Department-Team"""
		if self.department and self.team_name:
			# Format: S1-Product Listing-Team A
			self.name = f"{self.department}-{self.team_name}"
	
	def validate(self):
		"""Validate team"""
		# Auto-fill shift from department
		if self.department:
			dept = frappe.get_doc("CRM Department", self.department)
			self.shift = dept.shift
			
			# Verify department is enabled
			if not dept.enabled:
				frappe.throw(f"Department {dept.department_name} is disabled")
		
		# Check for duplicate team name in same department
		existing = frappe.db.exists("CRM Team", {
			"department": self.department,
			"team_name": self.team_name,
			"name": ["!=", self.name]
		})
		if existing:
			frappe.throw(f"Team '{self.team_name}' already exists in this department")
	
	def on_update(self):
		"""Update related users when team is updated"""
		# Update department and shift in all users under this team
		users = frappe.get_all("User", filters={"crm_team": self.name})
		for user in users:
			frappe.db.set_value("User", user.name, {
				"crm_department": self.department,
				"crm_shift": self.shift
			})


@frappe.whitelist()
def get_teams_by_department(department):
	"""Get all teams for a specific department"""
	return frappe.get_all(
		"CRM Team",
		filters={"department": department, "enabled": 1},
		fields=["name", "team_name", "department", "shift", "team_leader"]
	)


@frappe.whitelist()
def get_team_members(team):
	"""Get all members of a specific team"""
	return frappe.get_all(
		"User",
		filters={"crm_team": team, "enabled": 1},
		fields=["name", "full_name", "email", "crm_team", "crm_department", "crm_shift"]
	)
