# Copyright (c) 2026, IP CRM and contributors
# For license information, please see license.txt

"""
Override CRM's permission checks to accept department routing roles.

Patches:
1. crm.api.check_app_permission — app-level access
2. crm.utils.is_sales_user — used by @sales_user_only decorator (dashboard etc.)
3. crm.api.session.get_users — returns role info to the CRM Vue frontend
"""

import functools
import frappe


def _is_department_user(user=None):
	"""Check if the user has any department routing role."""
	check_user = user or frappe.session.user
	if check_user == "Administrator":
		return True

	roles = frappe.get_roles(check_user)
	dept_stages = frappe.get_all(
		"Department Pipeline Stage",
		filters={"enabled": 1},
		fields=["department_role", "manager_role"],
	)
	for stage in dept_stages:
		if stage.department_role in roles or stage.manager_role in roles:
			return True
	return False


def _is_department_manager(user=None):
	"""Check if the user has a department manager role."""
	check_user = user or frappe.session.user
	roles = frappe.get_roles(check_user)
	dept_stages = frappe.get_all(
		"Department Pipeline Stage",
		filters={"enabled": 1},
		fields=["manager_role"],
	)
	for stage in dept_stages:
		if stage.manager_role and stage.manager_role in roles:
			return True
	return False


def check_app_permission():
	"""
	Custom permission check for CRM app access.
	Allows access for standard CRM roles + department routing roles.
	"""
	if frappe.session.user == "Administrator":
		return True

	roles = frappe.get_roles()

	if any(role in ["System Manager", "Sales User", "Sales Manager"] for role in roles):
		return True

	return _is_department_user()


def patch_crm_permission():
	"""Monkey-patch CRM permission checks to include department role users."""

	# 1. Patch check_app_permission
	try:
		import crm.api as crm_api
		crm_api.check_app_permission = check_app_permission
	except ImportError:
		pass

	# 2. Patch is_sales_user — the @sales_user_only decorator resolves
	# this from crm.utils module globals at CALL TIME, so patching the
	# module attribute affects all already-decorated functions.
	try:
		import crm.utils as crm_utils

		_original_is_sales_user = getattr(crm_utils, '_original_is_sales_user', crm_utils.is_sales_user)

		def patched_is_sales_user(user=None):
			if _original_is_sales_user(user):
				return True
			return _is_department_user(user)

		# Store original to avoid double-wrapping on repeated calls
		if not hasattr(crm_utils, '_original_is_sales_user'):
			crm_utils._original_is_sales_user = _original_is_sales_user

		crm_utils.is_sales_user = patched_is_sales_user
	except ImportError:
		pass

	# 3. Patch get_users to recognize department users in the frontend
	try:
		import crm.api.session as session_module

		_original_get_users = getattr(session_module, '_original_get_users', session_module.get_users)

		@frappe.whitelist()
		def patched_get_users():
			result = _original_get_users()
			users_list, crm_users_list = result

			# Get department roles
			dept_stages = frappe.get_all(
				"Department Pipeline Stage",
				filters={"enabled": 1},
				fields=["department_role", "manager_role"],
			)
			dept_roles = set()
			mgr_roles = set()
			for stage in dept_stages:
				if stage.department_role:
					dept_roles.add(stage.department_role)
				if stage.manager_role:
					mgr_roles.add(stage.manager_role)

			crm_user_names = {u.name for u in crm_users_list}

			for user in users_list:
				user_roles = user.get("roles", [])
				if not user.get("role") and user_roles:
					# Set role for department managers/users
					if mgr_roles & set(user_roles):
						user["role"] = "Sales Manager"
					elif dept_roles & set(user_roles):
						user["role"] = "Sales User"

				# Add department users to crmUsers if not already there
				if user.name not in crm_user_names:
					if user_roles and (dept_roles | mgr_roles) & set(user_roles):
						crm_users_list.append(user)
						crm_user_names.add(user.name)

			return users_list, crm_users_list

		if not hasattr(session_module, '_original_get_users'):
			session_module._original_get_users = _original_get_users

		session_module.get_users = patched_get_users
	except ImportError:
		pass

	# 4. Unblock CRM module for department users
	try:
		user = frappe.session.user
		if user and user not in ("Administrator", "Guest") and _is_department_user(user):
			blocked = frappe.get_doc("User", user).get("block_modules", [])
			crm_blocked = [b for b in blocked if b.module == "CRM"]
			if crm_blocked:
				for b in crm_blocked:
					frappe.delete_doc("Block Module", b.name, ignore_permissions=True)
	except Exception:
		pass

	# 5. Patch hierarchy tree to filter for department routing users
	# (non-manager department users should only see their own dept/shift)
	try:
		import crm.api.hierarchy as hierarchy_module

		_original_get_hierarchy = getattr(
			hierarchy_module, '_original_get_hierarchy_tree',
			hierarchy_module.get_hierarchy_tree,
		)

		@frappe.whitelist()
		def patched_get_hierarchy_tree():
			current_user = frappe.session.user
			if current_user == "Administrator":
				return _original_get_hierarchy()

			user_roles = frappe.get_roles(current_user)

			# Check if user is already admin/manager — let original handle it
			if any(r in user_roles for r in ["System Manager", "Sales Manager"]):
				return _original_get_hierarchy()

			# Check if user is a department manager — full access
			if _is_department_manager(current_user):
				return _original_get_hierarchy()

			# Check if user is a department team member — filter hierarchy
			if _is_department_user(current_user):
				# Find which Department Pipeline Stages the user belongs to
				dept_stages = frappe.get_all(
					"Department Pipeline Stage",
					filters={"enabled": 1},
					fields=["name", "stage_name", "department_role", "manager_role"],
				)

				user_dept_names = set()
				for stage in dept_stages:
					if (stage.department_role and stage.department_role in user_roles) or \
					   (stage.manager_role and stage.manager_role in user_roles):
						user_dept_names.add(stage.name)

				if user_dept_names:
					# Get the full hierarchy and filter it
					full_tree = _original_get_hierarchy()
					filtered_tree = []

					for shift in full_tree:
						filtered_shift = dict(shift)
						filtered_depts = []

						for dept in shift.get("departments", []):
							# Check if this CRM Department maps to a routing stage
							# Match by department_name since CRM Department and 
							# Department Pipeline Stage may use different naming
							dept_name = dept.get("name", "")
							dept_display = dept.get("department_name", "")

							# Check if any user_dept stage name matches
							should_include = False
							for ud in user_dept_names:
								try:
									stage_doc = frappe.get_cached_doc("Department Pipeline Stage", ud)
									if (stage_doc.stage_name.lower() == dept_display.lower() or
										stage_doc.name.lower() == dept_name.lower()):
										should_include = True
										break
								except Exception:
									pass

							if should_include:
								filtered_depts.append(dept)

						if filtered_depts:
							filtered_shift["departments"] = filtered_depts
							filtered_tree.append(filtered_shift)

					# If filtering matched something, return filtered
					if filtered_tree:
						return filtered_tree

			# Fall back to original
			return _original_get_hierarchy()

		if not hasattr(hierarchy_module, '_original_get_hierarchy_tree'):
			hierarchy_module._original_get_hierarchy_tree = _original_get_hierarchy

		hierarchy_module.get_hierarchy_tree = patched_get_hierarchy_tree
	except ImportError:
		pass

	# 6. Patch dashboard metric filtering for department users
	# (ensure regular department users only see their own metrics)
	try:
		import crm.api.dashboard as dashboard_module
		from crm.utils import sales_user_only

		_original_get_dashboard = getattr(dashboard_module, '_original_get_dashboard', dashboard_module.get_dashboard)
		_original_get_chart = getattr(dashboard_module, '_original_get_chart', dashboard_module.get_chart)

		@frappe.whitelist()
		@functools.wraps(_original_get_dashboard)
		def patched_get_dashboard(from_date="", to_date="", user="", **kwargs):
			# If user is a regular department member but not a manager, force user filter
			if not user and _is_department_user() and not _is_department_manager():
				user = frappe.session.user
			return _original_get_dashboard(from_date=from_date, to_date=to_date, user=user, **kwargs)

		@frappe.whitelist()
		@functools.wraps(_original_get_chart)
		def patched_get_chart(name, type, from_date="", to_date="", user="", **kwargs):
			if not user and _is_department_user() and not _is_department_manager():
				user = frappe.session.user
			return _original_get_chart(name=name, type=type, from_date=from_date, to_date=to_date, user=user, **kwargs)

		if not hasattr(dashboard_module, '_original_get_dashboard'):
			dashboard_module._original_get_dashboard = _original_get_dashboard
			dashboard_module._original_get_chart = _original_get_chart

		dashboard_module.get_dashboard = patched_get_dashboard
		dashboard_module.get_chart = patched_get_chart

	except ImportError:
		pass

