"""
Patch to add department and sales_team custom fields to CRM Lead
For Facebook lead auto-distribution workflow
"""

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def execute():
	"""Add custom fields for department and sales team to CRM Lead"""
	
	if not frappe.get_meta("CRM Lead").has_field("department"):
		frappe.logger().info("Adding department and sales_team fields to CRM Lead")
		
		create_custom_fields(
			{
				"CRM Lead": [
					{
						"fieldname": "department",
						"fieldtype": "Link",
						"label": "Department",
						"options": "CRM Department",
						"insert_after": "lead_owner",
						"in_list_view": 0,
						"in_standard_filter": 1,
						"read_only": 0,
						"description": "Department assigned to this lead (e.g., Seller Onboarding)",
					},
					{
						"fieldname": "sales_team",
						"fieldtype": "Link",
						"label": "Sales Team",
						"options": "CRM Team",
						"insert_after": "department",
						"in_list_view": 1,
						"in_standard_filter": 1,
						"read_only": 0,
						"description": "Sales team assigned for lead distribution",
					},
					{
						"fieldname": "auto_distributed",
						"fieldtype": "Check",
						"label": "Auto Distributed",
						"insert_after": "sales_team",
						"default": "0",
						"read_only": 1,
						"description": "Indicates if this lead was automatically distributed to a team",
					},
					{
						"fieldname": "distribution_timestamp",
						"fieldtype": "Datetime",
						"label": "Distribution Timestamp",
						"insert_after": "auto_distributed",
						"read_only": 1,
						"description": "When the lead was distributed to a team",
					},
				]
			}
		)
		
		frappe.clear_cache(doctype="CRM Lead")
		frappe.logger().info("Successfully added department and sales_team fields to CRM Lead")
