# Copyright (c) 2026, IP CRM and contributors
# For license information, please see license.txt

"""
One-time setup script to seed default data for the Lead Routing System.

Run via: bench --site ipshopy.localhost execute lead_routing.setup.run_setup
"""

import frappe
from frappe import _


def run_setup():
	"""Main setup function — creates all default data."""
	frappe.flags.in_setup = True

	create_roles()
	create_department_stages()
	create_shifts()
	create_transition_rules()
	install_custom_fields()

	frappe.db.commit()
	frappe.flags.in_setup = False

	print("✅ Lead Routing setup completed successfully!")
	print("\nNext steps:")
	print("1. Create Assignment Rules in Frappe UI (one per department × shift)")
	print("2. Assign roles to users")
	print("3. Test by creating a new CRM Lead")


def create_roles():
	"""Create department-specific roles and grant CRM Lead access."""
	departments = [
		"Seller Onboarding",
		"Product Listing",
		"Google Ads",
		"Account Manager",
		"Completion",
	]

	for dept in departments:
		for role_type in ["User", "Manager"]:
			role_name = f"{dept} {role_type}"
			if not frappe.db.exists("Role", role_name):
				role = frappe.new_doc("Role")
				role.role_name = role_name
				role.desk_access = 1
				role.is_custom = 1
				role.insert(ignore_permissions=True)
				print(f"  Created role: {role_name}")

	# ── Grant CRM Lead DocPerm to each department role ──
	_ensure_crm_lead_permissions()

	print("  ✅ Department roles and CRM Lead permissions set up")


def _ensure_crm_lead_permissions():
	"""Ensure each department role has read/write access to CRM Lead."""
	departments = [
		"Seller Onboarding",
		"Product Listing",
		"Google Ads",
		"Account Manager",
		"Completion",
	]

	for dept in departments:
		for role_type in ["User", "Manager"]:
			role_name = f"{dept} {role_type}"

			# Check if a DocPerm entry already exists for this role
			exists = frappe.db.exists("DocPerm", {
				"parent": "CRM Lead",
				"role": role_name,
			})

			if not exists:
				# Add permission entry to CRM Lead doctype
				lead_doctype = frappe.get_doc("DocType", "CRM Lead")
				lead_doctype.append("permissions", {
					"role": role_name,
					"read": 1,
					"write": 1,
					"create": 1 if role_type == "Manager" else 0,
					"delete": 0,
					"email": 1,
					"print": 1,
					"report": 1,
					"export": 1 if role_type == "Manager" else 0,
				})
				lead_doctype.save(ignore_permissions=True)
				print(f"  Added CRM Lead permission for: {role_name}")



def create_department_stages():
	"""Create default department pipeline stages."""
	stages = [
		{
			"stage_name": "Seller Onboarding",
			"stage_order": 1,
			"is_terminal": 0,
			"department_role": "Seller Onboarding User",
			"manager_role": "Seller Onboarding Manager",
			"internal_statuses": "In Progress, Waiting for Client, Under Review",
			"enabled": 1,
		},
		{
			"stage_name": "Product Listing",
			"stage_order": 2,
			"is_terminal": 0,
			"department_role": "Product Listing User",
			"manager_role": "Product Listing Manager",
			"internal_statuses": "In Progress, Listing Pending, Quality Check",
			"enabled": 1,
		},
		{
			"stage_name": "Google Ads",
			"stage_order": 3,
			"is_terminal": 0,
			"department_role": "Google Ads User",
			"manager_role": "Google Ads Manager",
			"internal_statuses": "In Progress, Campaign Setup, Optimization",
			"enabled": 1,
		},
		{
			"stage_name": "Account Manager",
			"stage_order": 4,
			"is_terminal": 0,
			"department_role": "Account Manager User",
			"manager_role": "Account Manager Manager",
			"internal_statuses": "In Progress, Client Follow-up, Review",
			"enabled": 1,
		},
		{
			"stage_name": "Completion",
			"stage_order": 5,
			"is_terminal": 1,
			"department_role": "Completion User",
			"manager_role": "Completion Manager",
			"internal_statuses": "Completed",
			"enabled": 1,
		},
	]

	for stage_data in stages:
		if not frappe.db.exists("Department Pipeline Stage", stage_data["stage_name"]):
			stage = frappe.new_doc("Department Pipeline Stage")
			stage.update(stage_data)
			stage.insert(ignore_permissions=True)
			print(f"  Created stage: {stage_data['stage_name']} (order: {stage_data['stage_order']})")


def create_shifts():
	"""Create default shifts."""
	shifts = [
		{
			"shift_name": "Morning Shift",
			"start_time": "06:00:00",
			"end_time": "18:00:00",
			"enabled": 1,
		},
		{
			"shift_name": "Night Shift",
			"start_time": "18:00:00",
			"end_time": "06:00:00",
			"enabled": 1,
		},
	]

	for shift_data in shifts:
		if not frappe.db.exists("Department Shift", shift_data["shift_name"]):
			shift = frappe.new_doc("Department Shift")
			shift.update(shift_data)
			shift.insert(ignore_permissions=True)
			print(f"  Created shift: {shift_data['shift_name']} ({shift_data['start_time']} - {shift_data['end_time']})")


def create_transition_rules():
	"""Create default transition rules for the pipeline."""
	rules = []

	# Forward transitions: each stage → next stage
	forward_chain = [
		("Seller Onboarding", "Product Listing"),
		("Product Listing", "Google Ads"),
		("Google Ads", "Account Manager"),
		("Account Manager", "Completion"),
	]

	for from_s, to_s in forward_chain:
		rules.append({
			"from_stage": from_s,
			"to_stage": to_s,
			"transition_type": "Forward",
		})

	# Backward transitions: only to Product Listing
	backward_chain = [
		("Google Ads", "Product Listing"),
		("Account Manager", "Product Listing"),
	]

	for from_s, to_s in backward_chain:
		rules.append({
			"from_stage": from_s,
			"to_stage": to_s,
			"transition_type": "Backward",
		})

	# Reject transitions: every stage (except first) → first stage
	reject_from = ["Product Listing", "Google Ads", "Account Manager", "Completion"]
	for from_s in reject_from:
		rules.append({
			"from_stage": from_s,
			"to_stage": "Seller Onboarding",
			"transition_type": "Reject",
		})

	for rule_data in rules:
		rule_name = f"TR-{rule_data['from_stage']}-{rule_data['to_stage']}"
		if not frappe.db.exists("Department Transition Rule", rule_name):
			rule = frappe.new_doc("Department Transition Rule")
			rule.update(rule_data)
			rule.enabled = 1
			rule.insert(ignore_permissions=True)
			print(f"  Created transition: {rule_data['from_stage']} → {rule_data['to_stage']} ({rule_data['transition_type']})")


def install_custom_fields():
	"""Install custom fields on CRM Lead."""
	from lead_routing.install import create_custom_fields
	create_custom_fields()
	print("  Installed custom fields on CRM Lead")
