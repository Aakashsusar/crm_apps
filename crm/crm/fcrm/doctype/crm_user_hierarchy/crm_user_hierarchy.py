"""
Custom fields for User doctype to support Shift → Department → Team hierarchy
"""
import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def create_user_hierarchy_fields():
	"""Create custom fields in User doctype for hierarchy"""
	
	custom_fields = {
		"User": [
			{
				"fieldname": "crm_hierarchy_section",
				"fieldtype": "Section Break",
				"label": "CRM Hierarchy",
				"insert_after": "language"
			},
			{
				"fieldname": "crm_team",
				"fieldtype": "Link",
				"label": "Team",
				"options": "CRM Team",
				"insert_after": "crm_hierarchy_section"
			},
			{
				"fieldname": "crm_team_name",
				"fieldtype": "Data",
				"label": "Team Name",
				"fetch_from": "crm_team.team_name",
				"read_only": 1,
				"insert_after": "crm_team"
			},
			{
				"fieldname": "column_break_hierarchy",
				"fieldtype": "Column Break",
				"insert_after": "crm_team_name"
			},
			{
				"fieldname": "crm_department",
				"fieldtype": "Link",
				"label": "Department",
				"options": "CRM Department",
				"fetch_from": "crm_team.department",
				"read_only": 1,
				"insert_after": "column_break_hierarchy"
			},
			{
				"fieldname": "crm_department_name",
				"fieldtype": "Data",
				"label": "Department Name",
				"fetch_from": "crm_department.department_name",
				"read_only": 1,
				"insert_after": "crm_department"
			},
			{
				"fieldname": "column_break_shift",
				"fieldtype": "Column Break",
				"insert_after": "crm_department_name"
			},
			{
				"fieldname": "crm_shift",
				"fieldtype": "Link",
				"label": "Shift",
				"options": "CRM Shift",
				"fetch_from": "crm_team.shift",
				"read_only": 1,
				"insert_after": "column_break_shift"
			},
			{
				"fieldname": "crm_shift_name",
				"fieldtype": "Data",
				"label": "Shift Name",
				"fetch_from": "crm_shift.shift_name",
				"read_only": 1,
				"insert_after": "crm_shift"
			}
		]
	}
	
	create_custom_fields(custom_fields, update=True)


def execute():
	"""Execute on module installation"""
	create_user_hierarchy_fields()
