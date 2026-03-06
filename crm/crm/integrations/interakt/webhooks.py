"""
Interakt Webhook Handler
Handles incoming webhooks from Interakt for:
- Incoming messages
- Message status updates (delivered, read)
"""

import frappe
from frappe import _
import json


@frappe.whitelist(allow_guest=True)
def handle_webhook():
	"""
	Main webhook handler for Interakt events.
	Endpoint: /api/method/crm.integrations.interakt.webhooks.handle_webhook
	"""
	try:
		# Get webhook data
		data = frappe.request.get_data(as_text=True)
		webhook_data = json.loads(data) if data else frappe.local.form_dict
		
		# Log webhook for debugging
		frappe.logger().info(f"Interakt Webhook Received: {json.dumps(webhook_data, indent=2)}")
		
		# Get event type
		event_type = webhook_data.get("type")
		
		if event_type == "message_received":
			handle_message_received(webhook_data)
		elif event_type == "message_status_update":
			handle_status_update(webhook_data)
		else:
			frappe.logger().info(f"Unknown webhook type: {event_type}")
		
		return {"success": True, "message": "Webhook processed"}
		
	except Exception as e:
		frappe.log_error(
			title="Interakt Webhook Error",
			message=f"Error processing webhook: {str(e)}\nData: {frappe.request.get_data(as_text=True)}"
		)
		return {"success": False, "error": str(e)}


def handle_message_received(webhook_data):
	"""
	Handle incoming message from customer.
	
	Webhook format:
	{
		"type": "message_received",
		"data": {
			"customer": {
				"channel_phone_number": "917003705584",
				"traits": {"name": "John Doe", ...}
			},
			"message": {
				"id": "message-id",
				"message": "Hello!",
				"message_content_type": "Text",
				"media_url": null,
				"received_at_utc": "2022-06-03T05:57:57.359000"
			}
		}
	}
	"""
	try:
		data = webhook_data.get("data", {})
		customer = data.get("customer", {})
		message = data.get("message", {})
		
		# Extract phone number
		phone_number = customer.get("channel_phone_number", "")
		if not phone_number:
			frappe.logger().error("No phone number in webhook")
			return
		
		# Clean phone number (remove country code for matching)
		clean_phone = phone_number.lstrip("+")
		
		# Get default country code from settings
		settings = frappe.get_single("CRM Interakt Settings")
		default_country_code = settings.default_country_code or "+91"
		country_code_digits = default_country_code.lstrip("+")
		
		if clean_phone.startswith(country_code_digits):
			clean_phone = clean_phone[len(country_code_digits):]
		
		# Find lead/deal/contact by phone number
		reference_doctype, reference_docname = find_document_by_phone(clean_phone)
		
		if not reference_doctype:
			frappe.logger().error(f"WhatsApp Webhook Matching Failed: No document found for phone: {phone_number} (cleaned: {clean_phone})")
			return
		
		frappe.logger().info(f"WhatsApp Webhook Matched: {reference_doctype} {reference_docname} for phone: {phone_number}")
		
		# Extract message details
		message_id = message.get("id")
		message_text = message.get("message", "")
		content_type = message.get("message_content_type", "Text").lower()
		media_url = message.get("media_url")
		
		# Check if message already exists
		existing = frappe.db.exists("CRM WhatsApp Message", {"message_id": message_id})
		if existing:
			frappe.logger().info(f"Message {message_id} already exists")
			return
		
		# Create incoming message record
		doc = frappe.new_doc("CRM WhatsApp Message")
		doc.update({
			"message_id": message_id,
			"phone_number": clean_phone,
			"country_code": "+91",
			"status": "Received",
			"direction": "Incoming",
			"message_content": message_text,
			"media_url": media_url,
			"reference_doctype": reference_doctype,
			"reference_docname": reference_docname,
		})
		
		doc.insert(ignore_permissions=True)
		frappe.db.commit()
		
		frappe.logger().info(f"Incoming message saved: {doc.name}")
		
		# Send real-time update AFTER insert+commit so the frontend can fetch the message
		frappe.publish_realtime(
			"whatsapp_message",
			{
				"reference_doctype": reference_doctype,
				"reference_name": reference_docname,
			},
			after_commit=True,
		)
		
	except Exception as e:
		frappe.log_error(
			title="Error handling incoming message",
			message=f"Error: {str(e)}\nWebhook data: {json.dumps(webhook_data, indent=2)}"
		)


def handle_status_update(webhook_data):
	"""
	Handle message status updates (sent, delivered, read).
	
	Webhook format:
	{
		"type": "message_status_update",
		"data": {
			"message_id": "message-id",
			"status": "delivered",
			"delivered_at_utc": "2022-06-03T05:58:00.000000"
		}
	}
	"""
	try:
		data = webhook_data.get("data", {})
		message_id = data.get("message_id")
		status = data.get("status", "").lower()
		
		if not message_id:
			frappe.logger().error("No message_id in status update")
			return
		
		# Find message by message_id
		message_name = frappe.db.get_value(
			"CRM WhatsApp Message",
			{"message_id": message_id},
			"name"
		)
		
		if not message_name:
			frappe.logger().info(f"Message not found: {message_id}")
			return
		
		# Update status
		doc = frappe.get_doc("CRM WhatsApp Message", message_name)
		
		# Map Interakt status to our status
		status_map = {
			"sent": "Sent",
			"delivered": "Delivered",
			"read": "Read",
			"failed": "Failed"
		}
		
		new_status = status_map.get(status, "Sent")
		doc.status = new_status
		
		# Update timestamps
		if status == "delivered" and data.get("delivered_at_utc"):
			doc.delivered_at = data.get("delivered_at_utc")
		elif status == "read" and data.get("read_at_utc"):
			doc.read_at = data.get("read_at_utc")
		
		doc.save(ignore_permissions=True)
		frappe.db.commit()
		
		# Send real-time update
		frappe.publish_realtime(
			"whatsapp_message",
			{
				"reference_doctype": doc.reference_doctype,
				"reference_name": doc.reference_docname,
			},
			after_commit=True
		)
		
		frappe.logger().info(f"Status updated: {message_name} -> {new_status}")
		
	except Exception as e:
		frappe.log_error(
			title="Error handling status update",
			message=f"Error: {str(e)}\nWebhook data: {json.dumps(webhook_data, indent=2)}"
		)


def find_document_by_phone(phone_number):
	"""
	Find Lead/Deal/Contact by phone number.
	Returns: (doctype, docname) or (None, None)
	"""
	# Get default country code from settings
	settings = frappe.get_single("CRM Interakt Settings")
	default_country_code = settings.default_country_code or "+91"
	country_code_digits = default_country_code.lstrip("+")

	# Try different phone number formats
	phone_variants = [
		phone_number,
		phone_number.lstrip("0"),
		f"0{phone_number}",
		f"{default_country_code}{phone_number}",
		f"{country_code_digits}{phone_number}",
	]
	
	frappe.logger().info(f"Searching for document with phone variants: {phone_variants}")
	
	# Search in CRM Lead
	for variant in phone_variants:
		lead = frappe.db.get_value(
			"CRM Lead",
			{"mobile_no": variant},
			"name"
		)
		if lead:
			return ("CRM Lead", lead)
		
		# Also check phone field
		lead = frappe.db.get_value(
			"CRM Lead",
			{"phone": variant},
			"name"
		)
		if lead:
			return ("CRM Lead", lead)
	
	# Search in CRM Deal
	for variant in phone_variants:
		deal = frappe.db.get_value(
			"CRM Deal",
			{"mobile_no": variant},
			"name"
		)
		if deal:
			return ("CRM Deal", deal)
	
	# Search in Contact
	for variant in phone_variants:
		contact = frappe.db.get_value(
			"Contact",
			{"mobile_no": variant},
			"name"
		)
		if contact:
			return ("Contact", contact)
	
	return (None, None)
