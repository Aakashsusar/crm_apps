"""
Patch to add Facebook webhook configuration fields to FCRM Settings
For real-time Facebook lead webhook integration
"""

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def execute():
	"""Add Facebook webhook configuration fields to FCRM Settings"""
	
	if not frappe.get_meta("FCRM Settings").has_field("facebook_webhook_section"):
		frappe.logger().info("Adding Facebook webhook configuration fields to FCRM Settings")
		
		create_custom_fields(
			{
				"FCRM Settings": [
					{
						"fieldname": "facebook_integration_tab",
						"fieldtype": "Tab Break",
						"label": "Facebook Integration",
						"insert_after": "dropdown_items_tab",
					},
					{
						"fieldname": "facebook_webhook_section",
						"fieldtype": "Section Break",
						"label": "Webhook Configuration",
						"insert_after": "facebook_integration_tab",
						"description": "Configure Facebook Lead Ads webhook for real-time lead sync",
					},
					{
						"fieldname": "facebook_webhook_verify_token",
						"fieldtype": "Password",
						"label": "Webhook Verify Token",
						"insert_after": "facebook_webhook_section",
						"description": "Token used to verify webhook during Meta app setup. Generate a random string and use the same in Meta Developer Console.",
					},
					{
						"fieldname": "facebook_app_secret",
						"fieldtype": "Password",
						"label": "App Secret",
						"insert_after": "facebook_webhook_verify_token",
						"description": "Facebook App Secret from Meta Developer Console. Used to verify webhook request signatures.",
					},
					{
						"fieldname": "facebook_webhook_url",
						"fieldtype": "Data",
						"label": "Webhook URL",
						"insert_after": "facebook_app_secret",
						"read_only": 1,
						"description": "Copy this URL and paste it in Meta Developer Console webhook configuration",
					},
					{
						"fieldname": "facebook_webhook_info",
						"fieldtype": "HTML",
						"label": "Setup Instructions",
						"insert_after": "facebook_webhook_url",
						"options": """
							<div style="padding: 10px; background: #f8f9fa; border-radius: 4px; margin-top: 10px;">
								<h4>Setup Instructions:</h4>
								<ol>
									<li>Generate a random verify token (e.g., using a password generator)</li>
									<li>Enter the verify token above and save</li>
									<li>Copy the Webhook URL shown above</li>
									<li>Go to Meta Developer Console → Your App → Webhooks</li>
									<li>Add webhook subscription for "leadgen" events</li>
									<li>Paste the Webhook URL and verify token</li>
									<li>Enter your Facebook App Secret above</li>
									<li>Test the webhook by submitting a test lead</li>
								</ol>
							</div>
						""",
					},
				]
			}
		)
		
		frappe.clear_cache(doctype="FCRM Settings")
		frappe.logger().info("Successfully added Facebook webhook configuration fields to FCRM Settings")
