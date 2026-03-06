#!/bin/bash

# Script to update Interakt API files in WSL

echo "🔄 Updating Interakt API files in WSL..."

# Define the target directory
TARGET_DIR="/home/acash/frappe/frappe-bench/apps/crm/crm/integrations/interakt"

# Backup existing file
echo "📦 Creating backup..."
cp "$TARGET_DIR/api.py" "$TARGET_DIR/api.py.backup.$(date +%Y%m%d_%H%M%S)"

# Create the updated api.py content
cat > "$TARGET_DIR/api.py" << 'ENDOFFILE'
import frappe
from frappe import _

from .interakt_handler import Interakt
from .utils import (
	get_country_code_and_phone,
	get_lead_full_name,
	get_lead_phone_number,
)


def send_welcome_message_to_lead_hook(doc, method):
	"""
	Hook function called after a lead is inserted.
	Sends welcome message if enabled in settings.
	
	:param doc: CRM Lead document
	:param method: Method name (after_insert)
	"""
	# Check if Interakt is enabled and auto-send is enabled
	settings = frappe.get_single("CRM Interakt Settings")
	if not settings.enabled or not settings.send_welcome_on_lead_create:
		return
	
	# Send welcome message in background
	frappe.enqueue(
		"crm.integrations.interakt.api.send_welcome_message_to_lead",
		queue="default",
		timeout=300,
		lead_name=doc.name,
	)


@frappe.whitelist()
def is_enabled():
	"""Check if Interakt integration is enabled."""
	return frappe.db.get_single_value("CRM Interakt Settings", "enabled")


@frappe.whitelist()
def send_welcome_message_to_lead(lead_name):
	"""
	Send welcome message to a lead using the seller_registration template.
	This is called when a new lead is created.
	
	:param lead_name: Name of the CRM Lead document
	:return: Dict with success status and message_id
	"""
	interakt = Interakt.connect()
	if not interakt:
		return {"success": False, "error": "Interakt is not enabled"}

	try:
		# Get lead details
		phone_number = get_lead_phone_number(lead_name)
		if not phone_number:
			return {"success": False, "error": "Lead does not have a phone number"}

		full_name = get_lead_full_name(lead_name)
		if not full_name:
			full_name = "Seller"

		# Extract country code and phone number
		country_code, clean_phone = get_country_code_and_phone(
			phone_number, interakt.default_country_code
		)

		# Send template message
		result = interakt.send_template_message(
			phone_number=clean_phone,
			country_code=country_code,
			template_name="seller_registration",
			language_code="en",
			header_values=[
				"https://interaktprodmediastorage.blob.core.windows.net/mediaprodstoragecontainer/d4929d4d-7b6d-4044-b878-c3507ed788ba/message_template_sample/mmJTLZbwxohY/Ipshopy_Policies.pdf?se=2031-01-02T06%3A22%3A29Z&sp=rt&sv=2019-12-12&sr=b&sig=FJ0E76FRRDN9AYvS/Y8r7vsADDfb4lYiTHe4Y5YL0eY%3D"
			],
			body_values=[full_name],
			file_name="Ipshopy_Policies.pdf",
			callback_data=f"lead_welcome_{lead_name}",
		)

		if result.get("success"):
			# Create WhatsApp message log
			create_whatsapp_message_log(
				message_id=result.get("message_id"),
				phone_number=clean_phone,
				country_code=country_code,
				template_name="seller_registration",
				template_language="en",
				reference_doctype="CRM Lead",
				reference_docname=lead_name,
				sent_by=frappe.session.user,
				status="Sent",
			)

		return result

	except Exception as e:
		frappe.log_error(
			title="Error sending welcome message to lead",
			message=f"Lead: {lead_name}\nError: {str(e)}",
		)
		return {"success": False, "error": str(e)}


@frappe.whitelist()
def send_template_message(
	reference_doctype,
	reference_docname,
	phone_number,
	template_name,
	language_code="en",
	header_values=None,
	body_values=None,
	button_values=None,
	file_name=None,
):
	"""
	Send a WhatsApp template message via Interakt.
	
	:param reference_doctype: DocType to link message to (e.g., 'CRM Lead')
	:param reference_docname: Document name to link message to
	:param phone_number: Recipient phone number
	:param template_name: Template name from Interakt
	:param language_code: Language code (default: 'en')
	:param header_values: JSON string of header values
	:param body_values: JSON string of body values
	:param button_values: JSON string of button values
	:param file_name: File name for document headers
	:return: Dict with success status and message_id
	"""
	interakt = Interakt.connect()
	if not interakt:
		frappe.throw(_("Interakt is not enabled"))

	# Parse JSON strings
	import json

	if isinstance(header_values, str):
		header_values = json.loads(header_values) if header_values else None
	if isinstance(body_values, str):
		body_values = json.loads(body_values) if body_values else None
	if isinstance(button_values, str):
		button_values = json.loads(button_values) if button_values else None

	# Extract country code and phone number
	country_code, clean_phone = get_country_code_and_phone(
		phone_number, interakt.default_country_code
	)

	# Send message
	result = interakt.send_template_message(
		phone_number=clean_phone,
		country_code=country_code,
		template_name=template_name,
		language_code=language_code,
		header_values=header_values,
		body_values=body_values,
		button_values=button_values,
		file_name=file_name,
		callback_data=f"{reference_doctype}_{reference_docname}",
	)

	if result.get("success"):
		# Create WhatsApp message log
		create_whatsapp_message_log(
			message_id=result.get("message_id"),
			phone_number=clean_phone,
			country_code=country_code,
			template_name=template_name,
			template_language=language_code,
			reference_doctype=reference_doctype,
			reference_docname=reference_docname,
			sent_by=frappe.session.user,
			status="Sent",
		)

	return result


def create_whatsapp_message_log(
	message_id,
	phone_number,
	country_code,
	template_name,
	template_language,
	reference_doctype,
	reference_docname,
	sent_by,
	status="Pending",
	message_content=None,
):
	"""Create a WhatsApp message log entry."""
	try:
		doc = frappe.get_doc(
			{
				"doctype": "CRM WhatsApp Message",
				"message_id": message_id,
				"phone_number": phone_number,
				"country_code": country_code,
				"template_name": template_name,
				"template_language": template_language,
				"status": status,
				"direction": "Outgoing",
				"reference_doctype": reference_doctype,
				"reference_docname": reference_docname,
				"sent_by": sent_by,
				"message_content": message_content,
			}
		)
		doc.insert(ignore_permissions=True)
		frappe.db.commit()
		return doc.name
	except Exception as e:
		frappe.log_error(
			title="Error creating WhatsApp message log",
			message=f"Message ID: {message_id}\nError: {str(e)}",
		)
		return None


@frappe.whitelist()
def get_message_status(message_id):
	"""Get the status of a sent message."""
	if not message_id:
		return None

	message = frappe.db.get_value(
		"CRM WhatsApp Message",
		{"message_id": message_id},
		["name", "status", "sent_at", "delivered_at", "read_at"],
		as_dict=True,
	)

	return message


@frappe.whitelist()
def get_whatsapp_messages(reference_doctype, reference_docname):
	"""
	Get all WhatsApp messages for a specific document (Lead/Deal/Contact).
	Returns data in format compatible with frontend WhatsAppArea component.
	
	:param reference_doctype: DocType (e.g., 'CRM Lead')
	:param reference_docname: Document name (e.g., 'LEAD-00001')
	:return: List of messages in frontend-compatible format
	"""
	messages = frappe.get_all(
		"CRM WhatsApp Message",
		filters={
			"reference_doctype": reference_doctype,
			"reference_docname": reference_docname,
		},
		fields=[
			"name",
			"message_id",
			"phone_number",
			"country_code",
			"status",
			"direction",
			"template_name",
			"template_language",
			"message_content",
			"media_url",
			"sent_by",
			"creation",
			"sent_at",
			"delivered_at",
			"read_at",
		],
		order_by="creation asc",
	)

	# Transform to frontend format
	formatted_messages = []
	for msg in messages:
		formatted_msg = {
			"name": msg.name,
			"message_id": msg.message_id,
			"type": msg.direction,  # "Outgoing" or "Incoming"
			"to": f"{msg.country_code}{msg.phone_number}",
			"from": f"{msg.country_code}{msg.phone_number}" if msg.direction == "Incoming" else "",
			"content_type": "text" if not msg.media_url else "image",  # Simplified for now
			"message_type": "Template" if msg.template_name else "Text",
			"attach": msg.media_url or "",
			"template": msg.message_content if msg.template_name else "",
			"message": msg.message_content or "",
			"status": msg.status.lower() if msg.status else "pending",  # "sent", "delivered", "read"
			"creation": msg.creation,
			"reference_doctype": reference_doctype,
			"reference_name": reference_docname,
			"is_reply": False,  # TODO: Implement reply functionality
			"reply_to_message_id": None,
		}
		
		# Add template details if it's a template message
		if msg.template_name:
			formatted_msg["template_name"] = msg.template_name
			formatted_msg["header"] = ""  # TODO: Extract from template
			formatted_msg["footer"] = ""  # TODO: Extract from template
		
		formatted_messages.append(formatted_msg)

	return formatted_messages


@frappe.whitelist()
def send_text_message_to_lead(
	reference_doctype,
	reference_docname,
	message_text,
):
	"""
	Send a free text WhatsApp message to a lead/deal/contact.
	
	:param reference_doctype: DocType (e.g., 'CRM Lead')
	:param reference_docname: Document name (e.g., 'LEAD-00001')
	:param message_text: The text message to send
	:return: Dict with success status and message_id
	"""
	interakt = Interakt.connect()
	if not interakt:
		frappe.throw(_("Interakt is not enabled"))

	# Get phone number from the document
	doc = frappe.get_doc(reference_doctype, reference_docname)
	
	# Try to get phone number
	phone_number = None
	if hasattr(doc, 'mobile_no') and doc.mobile_no:
		phone_number = doc.mobile_no
	elif hasattr(doc, 'phone') and doc.phone:
		phone_number = doc.phone
	elif hasattr(doc, 'phone_number') and doc.phone_number:
		phone_number = doc.phone_number
	
	if not phone_number:
		frappe.throw(_("No phone number found for this {0}").format(reference_doctype))

	# Format phone number with country code
	if not phone_number.startswith('+'):
		phone_number = interakt.default_country_code + phone_number.lstrip('0')

	# Send message
	result = interakt.send_text_message(
		phone_number=phone_number,
		message_text=message_text,
		callback_data=f"{reference_doctype}_{reference_docname}",
	)

	if result.get("success"):
		# Create WhatsApp message log
		create_whatsapp_message_log(
			message_id=result.get("message_id"),
			phone_number=phone_number.lstrip('+').lstrip(interakt.default_country_code.lstrip('+')),
			country_code=interakt.default_country_code,
			template_name=None,
			template_language=None,
			reference_doctype=reference_doctype,
			reference_docname=reference_docname,
			sent_by=frappe.session.user,
			status="Sent",
			message_content=message_text,
		)

	return result
ENDOFFILE

echo "✅ File updated successfully!"
echo ""
echo "🔄 Now restart bench:"
echo "   cd ~/frappe/frappe-bench"
echo "   bench restart"
