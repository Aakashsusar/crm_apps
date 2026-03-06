"""
Custom fields for CRM Lead doctype to support Shift → Department → Team hierarchy
"""
import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def create_lead_hierarchy_fields():
	"""Create custom fields in CRM Lead doctype for hierarchy"""
	
	custom_fields = {
		"CRM Lead": [
			{
				"fieldname": "assignment_section",
				"fieldtype": "Section Break",
				"label": "Assignment & Hierarchy",
				"insert_after": "lead_owner"
			},
			{
				"fieldname": "assigned_team",
				"fieldtype": "Link",
				"label": "Assigned Team",
				"options": "CRM Team",
				"insert_after": "assignment_section"
			},
			{
				"fieldname": "assigned_department",
				"fieldtype": "Link",
				"label": "Assigned Department",
				"options": "CRM Department",
				"fetch_from": "assigned_team.department",
				"read_only": 1,
				"insert_after": "assigned_team"
			},
			{
				"fieldname": "column_break_assignment",
				"fieldtype": "Column Break",
				"insert_after": "assigned_department"
			},
			{
				"fieldname": "assigned_shift",
				"fieldtype": "Link",
				"label": "Assigned Shift",
				"options": "CRM Shift",
				"fetch_from": "assigned_team.shift",
				"read_only": 1,
				"insert_after": "column_break_assignment"
			}
		]
	}
	
	create_custom_fields(custom_fields, update=True)


def execute():
	"""Execute on module installation"""
	create_lead_hierarchy_fields()
