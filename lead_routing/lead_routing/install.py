# Copyright (c) 2026, IP CRM and contributors
# For license information, please see license.txt

import frappe


def after_install():
	"""Create custom fields on CRM Lead for department routing."""
	create_custom_fields()


def create_custom_fields():
	"""Add routing-related custom fields to CRM Lead."""
	from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

	custom_fields = {
		"CRM Lead": [
			{
				"fieldname": "routing_tab",
				"fieldtype": "Tab Break",
				"label": "Routing",
				"insert_after": "syncing_tab",
				"module": "Lead Routing",
			},
			{
				"fieldname": "current_department",
				"fieldtype": "Link",
				"label": "Current Department",
				"options": "Department Pipeline Stage",
				"insert_after": "routing_tab",
				"in_list_view": 1,
				"in_standard_filter": 1,
				"read_only": 1,
				"search_index": 1,
				"module": "Lead Routing",
			},
			{
				"fieldname": "current_shift",
				"fieldtype": "Link",
				"label": "Shift",
				"options": "Department Shift",
				"insert_after": "current_department",
				"in_standard_filter": 1,
				"read_only": 1,
				"search_index": 1,
				"module": "Lead Routing",
			},
			{
				"fieldname": "department_status",
				"fieldtype": "Select",
				"label": "Department Status",
				"options": "\nWorking\nDone\nRejected",
				"insert_after": "current_shift",
				"in_list_view": 1,
				"in_standard_filter": 1,
				"read_only": 1,
				"module": "Lead Routing",
			},
			{
				"fieldname": "routing_section",
				"fieldtype": "Section Break",
				"label": "Department History",
				"insert_after": "department_status",
				"module": "Lead Routing",
			},
			{
				"fieldname": "department_history",
				"fieldtype": "Table",
				"label": "Department History",
				"options": "Lead Department Log",
				"insert_after": "routing_section",
				"read_only": 1,
				"module": "Lead Routing",
			},
		]
	}

	create_custom_fields(custom_fields, update=True)
	frappe.db.commit()
