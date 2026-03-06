import json
import re

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
	
	# Send welcome message directly (not enqueued to avoid job queue issues)
	try:
		send_welcome_message_to_lead(doc.name)
	except Exception as e:
		frappe.log_error(
			title="Error in welcome message hook",
			message=f"Lead: {doc.name}\nError: {str(e)}"
		)


@frappe.whitelist()
def is_enabled():
	"""Check if Interakt integration is enabled."""
	return frappe.db.get_single_value("CRM Interakt Settings", "enabled")


@frappe.whitelist()
def send_welcome_message_to_lead(lead_name):
	"""
	Send welcome message to a lead using template from settings.
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

		# Get template settings from CRM Interakt Settings
		settings = frappe.get_single("CRM Interakt Settings")
		welcome_template = getattr(settings, "welcome_template_name", None) or "seller_registration"
		welcome_header_url = getattr(settings, "welcome_header_url", None) or ""
		welcome_header_filename = getattr(settings, "welcome_header_filename", None) or ""

		# Build header_values and file_name only if configured
		header_values = [welcome_header_url] if welcome_header_url else None
		file_name = welcome_header_filename if welcome_header_filename else None

		# Send template message
		result = interakt.send_template_message(
			phone_number=clean_phone,
			country_code=country_code,
			template_name=welcome_template,
			language_code="en",
			header_values=header_values,
			body_values=[full_name],
			file_name=file_name,
			callback_data=f"lead_welcome_{lead_name}",
		)

		if result.get("success"):
			# Create WhatsApp message log
			create_whatsapp_message_log(
				message_id=result.get("message_id"),
				phone_number=clean_phone,
				country_code=country_code,
				template_name=welcome_template,
				template_language="en",
				reference_doctype="CRM Lead",
				reference_docname=lead_name,
				sent_by=frappe.session.user,
				status="Sent",
			)

			# Publish real-time event
			frappe.publish_realtime("whatsapp_message", {
				"reference_doctype": "CRM Lead",
				"reference_name": lead_name,
			})

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

		# Publish real-time event
		frappe.publish_realtime("whatsapp_message", {
			"reference_doctype": reference_doctype,
			"reference_name": reference_docname,
		})

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
			"is_reply": False,
			"reply_to_message_id": None,
		}
		
		# Add template details if it's a template message
		if msg.template_name:
			formatted_msg["template_name"] = msg.template_name
			# Look up full template body from WhatsApp Templates for hover preview
			tpl_body = ""
			tpl_header = ""
			tpl_footer = ""
			if frappe.db.exists("WhatsApp Templates", msg.template_name):
				tpl = frappe.get_doc("WhatsApp Templates", msg.template_name)
				tpl_body = tpl.body_text or tpl.template or ""
				tpl_header = tpl.header_text or ""
				tpl_footer = tpl.footer or ""
			formatted_msg["template_body"] = tpl_body
			formatted_msg["header"] = tpl_header
			formatted_msg["footer"] = tpl_footer
		
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
	frappe.logger().info(f"Original phone number from doc: {phone_number}")
	if not phone_number.startswith('+'):
		phone_number = interakt.default_country_code + phone_number.lstrip('0')
	frappe.logger().info(f"Formatted phone number for Interakt: {phone_number}")

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

		# Publish real-time event
		frappe.publish_realtime("whatsapp_message", {
			"reference_doctype": reference_doctype,
			"reference_name": reference_docname,
		})

	return result


@frappe.whitelist()
def fetch_interakt_templates(offset=0, autosubmitted_for="all", language="all"):
	"""
	Fetch WhatsApp templates from Interakt API and return raw data.
	"""
	interakt = Interakt.connect()
	if not interakt:
		frappe.throw(_("Interakt is not enabled"))

	result = interakt.get_templates(
		offset=int(offset),
		autosubmitted_for=autosubmitted_for,
		language=language,
	)

	# Log raw JSON response to console
	print("="*80)
	print("[INTERAKT FETCH TEMPLATES] Raw API Response:")
	print(json.dumps(result, indent=2, default=str))
	print("="*80)
	frappe.logger().info(f"[INTERAKT FETCH TEMPLATES] Response: {json.dumps(result, indent=2, default=str)}")

	if not result.get("success"):
		return {
			"success": False,
			"error": result.get("error", "Failed to fetch templates"),
			"templates": [],
		}

	# Extract actual template list from nested response
	templates = _extract_templates_from_response(result)
	return {
		"success": True,
		"templates": templates,
		"count": len(templates),
	}


def _extract_templates_from_response(result):
	"""
	Extract the actual template list from Interakt's nested response.
	Interakt returns: {templates: [{count: N, results: {templates: [...]}}]}
	"""
	raw_templates = result.get("templates", [])

	# Case 1: Nested structure — templates[0].results.templates
	if (
		raw_templates
		and isinstance(raw_templates, list)
		and len(raw_templates) > 0
		and isinstance(raw_templates[0], dict)
		and "results" in raw_templates[0]
	):
		inner = raw_templates[0].get("results", {})
		if isinstance(inner, dict) and "templates" in inner:
			return inner["templates"]

	# Case 2: Flat list of template dicts
	if raw_templates and isinstance(raw_templates, list) and isinstance(raw_templates[0], dict) and "name" in raw_templates[0]:
		return raw_templates

	return []


def _count_body_variables(body_text):
	"""Count the number of {{n}} variables in a template body."""
	if not body_text:
		return 0
	matches = re.findall(r"\{\{(\d+)\}\}", body_text)
	return max([int(m) for m in matches]) if matches else 0


def _normalize_buttons(buttons_raw):
	"""Normalize the buttons field from Interakt to a clean JSON string."""
	if not buttons_raw:
		return None
	# Interakt returns buttons as a JSON-encoded string sometimes double-escaped
	if isinstance(buttons_raw, str):
		try:
			parsed = json.loads(buttons_raw)
			# If the result is still a string, try parsing again (double-encoded)
			if isinstance(parsed, str):
				parsed = json.loads(parsed)
			return json.dumps(parsed)
		except (json.JSONDecodeError, TypeError):
			return buttons_raw
	return json.dumps(buttons_raw)


@frappe.whitelist()
def sync_interakt_templates():
	"""
	Sync WhatsApp templates from Interakt to local WhatsApp Templates doctype.
	Fetches all templates and upserts them locally.
	"""
	interakt = Interakt.connect()
	if not interakt:
		frappe.throw(_("Interakt is not enabled"))

	result = interakt.get_templates()

	# Log raw JSON response to console
	print("="*80)
	print("[INTERAKT SYNC TEMPLATES] Raw API Response:")
	print(json.dumps(result, indent=2, default=str))
	print("="*80)
	frappe.logger().info(f"[INTERAKT SYNC TEMPLATES] Response: {json.dumps(result, indent=2, default=str)}")

	if not result.get("success"):
		return {
			"success": False,
			"error": result.get("error", "Failed to fetch templates from Interakt"),
		}

	# Extract actual template list from nested response
	templates = _extract_templates_from_response(result)
	print(f"[INTERAKT SYNC] Extracted {len(templates)} templates to sync")
	synced = 0
	errors = []

	for tpl in templates:
		try:
			template_name = tpl.get("name") or tpl.get("display_name")
			if not template_name:
				continue

			body_text = tpl.get("body") or ""
			variable_count = _count_body_variables(body_text)
			buttons_json = _normalize_buttons(tpl.get("buttons"))

			# Map Interakt approval_status to local status
			approval_status = tpl.get("approval_status", "")
			status_map = {
				"APPROVED": "APPROVED",
				"PENDING": "PENDING",
				"REJECTED": "REJECTED",
			}
			local_status = status_map.get(approval_status, approval_status or "PENDING")

			# Map header_format
			header_format = tpl.get("header_format") or ""
			if header_format and header_format.upper() in ("TEXT", "IMAGE", "DOCUMENT", "VIDEO"):
				header_format = header_format.upper()
			else:
				header_format = ""

			values = {
				"status": local_status,
				"category": tpl.get("category") or "",
				"language_code": tpl.get("language") or "en",
				"template": body_text,
				"body_text": body_text,
				"footer": tpl.get("footer") or "",
				"header_text": tpl.get("header") or "",
				"header_type": header_format or "",
				"header_format": header_format,
				"interakt_template_id": tpl.get("id") or "",
				"buttons": buttons_json or "",
				"variable_count": variable_count,
				"last_synced": frappe.utils.now(),
			}

			if frappe.db.exists("WhatsApp Templates", template_name):
				doc = frappe.get_doc("WhatsApp Templates", template_name)
				doc.update(values)
				doc.save(ignore_permissions=True)
			else:
				doc = frappe.get_doc({
					"doctype": "WhatsApp Templates",
					"template_name": template_name,
					**values,
				})
				doc.insert(ignore_permissions=True)

			synced += 1

		except Exception as e:
			tpl_name = tpl.get("name", "unknown")
			frappe.log_error(
				title=f"Error syncing template: {tpl_name}",
				message=str(e),
			)
			errors.append(f"{tpl_name}: {str(e)}")

	frappe.db.commit()

	return {
		"success": True,
		"synced": synced,
		"total": len(templates),
		"errors": errors,
	}

