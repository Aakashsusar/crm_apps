app_name = "lead_routing"
app_title = "Lead Routing"
app_publisher = "IP CRM"
app_description = "Department Based Lead Routing System"
app_email = "susaraakash4@gmail.com"
app_license = "mit"

# Required Apps
# required_apps = ["crm"]

# ──────────────────────────────────────────────────────────────────────────────
# Default redirect: department users go to CRM, not Desk
# ──────────────────────────────────────────────────────────────────────────────

default_home = "/crm"

# ──────────────────────────────────────────────────────────────────────────────
# Installation
# ──────────────────────────────────────────────────────────────────────────────

after_install = "lead_routing.install.after_install"

# ──────────────────────────────────────────────────────────────────────────────
# Client Scripts — INJECTED into CRM Lead form
# ──────────────────────────────────────────────────────────────────────────────

doctype_js = {
	"CRM Lead": "public/js/crm_lead_routing.js"
}

# ──────────────────────────────────────────────────────────────────────────────
# Document Events
# ──────────────────────────────────────────────────────────────────────────────

doc_events = {
	"CRM Lead": {
		"after_insert": "lead_routing.api.lead_transfer.on_lead_created",
		"validate": "lead_routing.api.lead_transfer.on_lead_validate",
	}
}

# ──────────────────────────────────────────────────────────────────────────────
# Permissions
# ──────────────────────────────────────────────────────────────────────────────

permission_query_conditions = {
	"CRM Lead": "lead_routing.api.permissions.get_permission_query",
}

has_permission = {
	"CRM Lead": "lead_routing.api.permissions.has_permission",
}

# ──────────────────────────────────────────────────────────────────────────────
# Fixtures (export custom fields with the app)
# ──────────────────────────────────────────────────────────────────────────────

fixtures = [
	{
		"dt": "Custom Field",
		"filters": [["module", "=", "Lead Routing"]],
	},
	{
		"dt": "Role",
		"filters": [["is_custom", "=", 1], ["name", "like", "%Onboarding%"]],
	},
	{
		"dt": "Role",
		"filters": [["is_custom", "=", 1], ["name", "like", "%Product Listing%"]],
	},
	{
		"dt": "Role",
		"filters": [["is_custom", "=", 1], ["name", "like", "%Google Ads%"]],
	},
	{
		"dt": "Role",
		"filters": [["is_custom", "=", 1], ["name", "like", "%Account Manager%"]],
	},
	{
		"dt": "Role",
		"filters": [["is_custom", "=", 1], ["name", "like", "%Completion%"]],
	},
]

# ──────────────────────────────────────────────────────────────────────────────
# Override CRM's app permission check to accept department roles
# (monkey-patches crm.api.check_app_permission on every request)
# ──────────────────────────────────────────────────────────────────────────────

on_session_creation = "lead_routing.api.crm_access.patch_crm_permission"
before_request = ["lead_routing.api.crm_access.patch_crm_permission"]

# ──────────────────────────────────────────────────────────────────────────────
# Scheduled Tasks
# ──────────────────────────────────────────────────────────────────────────────

# scheduler_events = {}

# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True
