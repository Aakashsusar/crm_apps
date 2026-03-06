import frappe


def get_interakt_whatsapp_number(user):
	"""Get the WhatsApp number configured for a user in Telephony Agent settings."""
	if not user:
		return None
	
	agent = frappe.db.get_value(
		"CRM Telephony Agent",
		user,
		["interakt_whatsapp_number", "interakt"],
		as_dict=True,
	)
	
	if agent and agent.get("interakt") and agent.get("interakt_whatsapp_number"):
		return agent.get("interakt_whatsapp_number")
	
	return None


def clean_phone_number(phone):
	"""Clean phone number by removing non-digit characters."""
	if not phone:
		return None
	return "".join(filter(str.isdigit, str(phone)))


def get_country_code_and_phone(phone_number, default_country_code="+91"):
	"""
	Extract country code and phone number from a full phone number.
	
	:param phone_number: Full phone number (e.g., '+919876543210' or '9876543210')
	:param default_country_code: Default country code if not present
	:return: Tuple of (country_code, phone_number)
	"""
	if not phone_number:
		return default_country_code, None
	
	phone_number = str(phone_number).strip()
	
	# If starts with +, extract country code
	if phone_number.startswith("+"):
		# Find where digits start after +
		for i, char in enumerate(phone_number[1:], 1):
			if not char.isdigit():
				continue
		
		# Common country code lengths: 1-3 digits
		if len(phone_number) > 10:
			# Try to extract country code (1-3 digits after +)
			for length in [3, 2, 1]:
				potential_code = phone_number[:length + 1]  # +XX or +XXX
				remaining = phone_number[length + 1:]
				if len(clean_phone_number(remaining)) >= 10:
					return potential_code, clean_phone_number(remaining)
		
		# If can't determine, use default
		return default_country_code, clean_phone_number(phone_number[1:])
	
	# No country code present
	return default_country_code, clean_phone_number(phone_number)


def get_lead_phone_number(lead_name):
	"""Get phone number from lead."""
	lead = frappe.get_doc("CRM Lead", lead_name)
	return lead.mobile_no or lead.phone


def get_lead_full_name(lead_name):
	"""Get full name from lead."""
	lead = frappe.get_doc("CRM Lead", lead_name)
	return " ".join(filter(None, [lead.first_name, lead.last_name]))
