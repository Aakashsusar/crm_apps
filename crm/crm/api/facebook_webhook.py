"""
Real-time Facebook Lead Ads Webhook Handler
Handles incoming leads from Meta Business Suite (Ipshopy Leads app)
"""

import frappe
import hmac
import hashlib
import json
from frappe import _


@frappe.whitelist(allow_guest=True, methods=["GET", "POST"])
def facebook_leadgen_webhook():
	"""
	Webhook endpoint for Facebook Lead Ads
	Meta will call this endpoint when new leads are generated
	
	GET: Webhook verification (Meta setup)
	POST: Receive lead data in real-time
	"""
	if frappe.request.method == "GET":
		return verify_webhook()
	elif frappe.request.method == "POST":
		return handle_lead_webhook()


def verify_webhook():
	"""
	Verify webhook during Meta app setup
	Meta sends: hub.mode, hub.verify_token, hub.challenge
	"""
	mode = frappe.request.args.get("hub.mode")
	token = frappe.request.args.get("hub.verify_token")
	challenge = frappe.request.args.get("hub.challenge")
	
	# Get verify token from settings (you'll need to configure this)
	verify_token = frappe.db.get_single_value("FCRM Settings", "facebook_webhook_verify_token")
	
	if not verify_token:
		frappe.log_error(
			"Facebook webhook verify token not configured in FCRM Settings",
			"Facebook Webhook Verification Failed"
		)
		frappe.throw(_("Webhook verification token not configured"))
	
	if mode == "subscribe" and token == verify_token:
		frappe.response["type"] = "text"
		return challenge
	else:
		frappe.throw(_("Webhook verification failed"), frappe.ValidationError)


def handle_lead_webhook():
	"""
	Process incoming lead data from Facebook
	Payload structure from Meta:
	{
		"entry": [{
			"id": "page_id",
			"time": timestamp,
			"changes": [{
				"field": "leadgen",
				"value": {
					"ad_id": "...",
					"form_id": "...",
					"leadgen_id": "...",
					"created_time": timestamp,
					"page_id": "...",
					"adgroup_id": "..."
				}
			}]
		}]
	}
	"""
	try:
		# Verify request signature for security
		if not verify_signature():
			frappe.log_error(
				"Invalid signature in Facebook webhook request",
				"Facebook Webhook Security Error"
			)
			return {"status": "error", "message": "Invalid signature"}
		
		# Parse webhook payload
		payload = frappe.request.get_data(as_text=True)
		data = json.loads(payload)
		
		# Log raw payload for debugging
		frappe.logger().info(f"Facebook webhook received: {payload}")
		
		# Process each entry
		for entry in data.get("entry", []):
			for change in entry.get("changes", []):
				if change.get("field") == "leadgen":
					process_leadgen_event(change.get("value"))
		
		return {"status": "success"}
		
	except Exception as e:
		frappe.log_error(
			f"Error processing Facebook webhook: {str(e)}\n{frappe.get_traceback()}",
			"Facebook Webhook Error"
		)
		return {"status": "error", "message": str(e)}


def verify_signature():
	"""
	Verify that the request came from Facebook using HMAC SHA256
	"""
	signature = frappe.request.headers.get("X-Hub-Signature-256", "")
	
	if not signature:
		return False
	
	# Get app secret from settings
	app_secret = frappe.db.get_single_value("FCRM Settings", "facebook_app_secret")
	
	if not app_secret:
		frappe.log_error(
			"Facebook app secret not configured in FCRM Settings",
			"Facebook Webhook Security Error"
		)
		return False
	
	# Calculate expected signature
	payload = frappe.request.get_data()
	expected_signature = "sha256=" + hmac.new(
		app_secret.encode("utf-8"),
		payload,
		hashlib.sha256
	).hexdigest()
	
	return hmac.compare_digest(signature, expected_signature)


def process_leadgen_event(value):
	"""
	Process a single leadgen event
	Fetch full lead data from Facebook Graph API and create CRM Lead
	"""
	leadgen_id = value.get("leadgen_id")
	form_id = value.get("form_id")
	page_id = value.get("page_id")
	
	if not leadgen_id or not form_id:
		frappe.log_error(
			f"Missing leadgen_id or form_id in webhook payload: {value}",
			"Facebook Webhook Data Error"
		)
		return
	
	# Check if form is configured for syncing
	form_exists = frappe.db.exists("Facebook Lead Form", form_id)
	if not form_exists:
		frappe.log_error(
			f"Facebook Lead Form {form_id} not found in system. Please sync forms first.",
			"Facebook Webhook Configuration Error"
		)
		return
	
	# Get the Lead Sync Source for this form
	sync_source = frappe.db.get_value(
		"Lead Sync Source",
		{"facebook_lead_form": form_id, "enabled": 1},
		["name", "access_token"],
		as_dict=True
	)
	
	if not sync_source:
		frappe.log_error(
			f"No enabled Lead Sync Source found for form {form_id}",
			"Facebook Webhook Configuration Error"
		)
		return
	
	# Fetch full lead data from Facebook Graph API
	from crm.lead_syncing.doctype.lead_sync_source.facebook import FacebookSyncSource
	
	fb_sync = FacebookSyncSource(
		access_token=frappe.get_doc("Lead Sync Source", sync_source.name).get_password("access_token"),
		form_id=form_id,
		source_name=sync_source.name
	)
	
	# Fetch single lead data
	lead_data = fb_sync.fetch_single_lead(leadgen_id)
	
	if lead_data:
		# Create lead in CRM (with validation and auto-distribution)
		fb_sync.sync_single_lead(lead_data, raise_exception=False)
		frappe.logger().info(f"Successfully created CRM Lead from Facebook leadgen_id: {leadgen_id}")
	else:
		frappe.log_error(
			f"Failed to fetch lead data for leadgen_id: {leadgen_id}",
			"Facebook API Error"
		)


@frappe.whitelist()
def test_webhook_endpoint():
	"""
	Test endpoint to verify webhook is accessible
	"""
	return {
		"status": "ok",
		"message": "Facebook webhook endpoint is active",
		"endpoint": frappe.utils.get_url() + "/api/method/crm.api.facebook_webhook.facebook_leadgen_webhook"
	}
