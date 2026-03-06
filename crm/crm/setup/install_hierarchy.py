"""
Installation script for CRM Hierarchy
Run this after installing the module to create custom fields
"""
import frappe


def execute():
	"""Execute installation"""
	print("Installing CRM Hierarchy...")
	
	# Create custom fields for User
	from crm.fcrm.doctype.crm_user_hierarchy.crm_user_hierarchy import create_user_hierarchy_fields
	create_user_hierarchy_fields()
	print("✓ User hierarchy fields created")
	
	# Create custom fields for CRM Lead
	from crm.fcrm.doctype.crm_lead_hierarchy.crm_lead_hierarchy import create_lead_hierarchy_fields
	create_lead_hierarchy_fields()
	print("✓ Lead hierarchy fields created")
	
	# Create sample data (optional)
	create_sample_shifts()
	
	frappe.db.commit()
	print("✓ CRM Hierarchy installation complete!")


def create_sample_shifts():
	"""Create sample shifts for testing"""
	
	shifts = [
		{
			"shift_name": "First Shift",
			"shift_code": "S1",
			"start_time": "07:00:00",
			"end_time": "16:00:00",
			"description": "Morning shift - 7 AM to 4 PM"
		},
		{
			"shift_name": "General Shift",
			"shift_code": "GEN",
			"start_time": "09:30:00",
			"end_time": "18:30:00",
			"description": "General shift - 9:30 AM to 6:30 PM"
		},
		{
			"shift_name": "Second Shift",
			"shift_code": "S2",
			"start_time": "16:00:00",
			"end_time": "01:00:00",
			"description": "Evening shift - 4 PM to 1 AM"
		}
	]
	
	for shift_data in shifts:
		if not frappe.db.exists("CRM Shift", shift_data["shift_name"]):
			shift = frappe.new_doc("CRM Shift")
			shift.update(shift_data)
			shift.insert(ignore_permissions=True)
			print(f"  ✓ Created shift: {shift_data['shift_name']}")
