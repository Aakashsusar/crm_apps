import frappe
from frappe.model.document import Document


class CRMDepartment(Document):
	"""CRM Department"""
	
	def autoname(self):
		"""Auto-generate name as Shift-Department"""
		if self.shift and self.department_name:
			shift_doc = frappe.get_doc("CRM Shift", self.shift)
			shift_code = shift_doc.shift_code or shift_doc.shift_name
			# Format: S1-Product Listing, GEN-Product Listing
			self.name = f"{shift_code}-{self.department_name}"
	
	def validate(self):
		"""Validate department"""
		# Verify shift exists and is enabled
		if self.shift:
			shift = frappe.get_doc("CRM Shift", self.shift)
			if not shift.enabled:
				frappe.throw(f"Shift {shift.shift_name} is disabled")
		
		# Check for duplicate department name in same shift
		existing = frappe.db.exists("CRM Department", {
			"shift": self.shift,
			"department_name": self.department_name,
			"name": ["!=", self.name]
		})
		if existing:
			frappe.throw(f"Department '{self.department_name}' already exists in this shift")
	
	def on_update(self):
		"""Update related teams when department is updated"""
		# Update shift in all teams under this department
		teams = frappe.get_all("CRM Team", filters={"department": self.name})
		for team in teams:
			frappe.db.set_value("CRM Team", team.name, "shift", self.shift)


@frappe.whitelist()
def get_departments_by_shift(shift):
	"""Get all departments for a specific shift"""
	return frappe.get_all(
		"CRM Department",
		filters={"shift": shift, "enabled": 1},
		fields=["name", "department_name", "shift", "department_head"]
	)
