import frappe
import requests
from frappe import _
from frappe.utils.password import get_decrypted_password


class Interakt:
	"""Interakt connector for WhatsApp messaging."""

	def __init__(self, settings):
		"""
		:param settings: `CRM Interakt Settings` doctype
		"""
		self.settings = settings
		self.api_key = settings.get_password("api_key")
		self.base_url = "https://api.interakt.ai/v1"
		self.default_country_code = settings.default_country_code or "+91"

	@classmethod
	def connect(cls):
		"""Make an Interakt connection."""
		settings = frappe.get_doc("CRM Interakt Settings")
		if not (settings and settings.enabled):
			return None
		return Interakt(settings=settings)

	def send_template_message(
		self,
		phone_number,
		country_code=None,
		template_name=None,
		language_code="en",
		header_values=None,
		body_values=None,
		button_values=None,
		file_name=None,
		callback_data=None,
		campaign_id=None,
	):
		"""
		Send a WhatsApp template message via Interakt API.
		
		:param phone_number: Phone number without country code
		:param country_code: Country code (default: from settings)
		:param template_name: Template name/code from Interakt
		:param language_code: Language code (default: 'en')
		:param header_values: List of header variable values
		:param body_values: List of body variable values
		:param button_values: Dict of button values {button_index: [values]}
		:param file_name: File name for document headers
		:param callback_data: Optional callback data
		:param campaign_id: Optional campaign ID for tracking
		:return: Response dict with message_id
		"""
		if not self.api_key:
			frappe.throw(_("Interakt API Key is not configured"))

		# Clean phone number (remove spaces, dashes, etc.)
		phone_number = "".join(filter(str.isdigit, str(phone_number)))
		
		# Use provided country code or default
		country_code = country_code or self.default_country_code

		# Prepare request payload
		payload = {
			"countryCode": country_code,
			"phoneNumber": phone_number,
			"type": "Template",
			"template": {
				"name": template_name,
				"languageCode": language_code,
			},
		}

		# Add optional fields
		if callback_data:
			payload["callbackData"] = callback_data

		if campaign_id:
			payload["campaignId"] = campaign_id

		# Add template parameters
		if header_values:
			payload["template"]["headerValues"] = header_values

		if body_values:
			payload["template"]["bodyValues"] = body_values

		if button_values:
			payload["template"]["buttonValues"] = button_values

		if file_name:
			payload["template"]["fileName"] = file_name

		# Make API request
		url = f"{self.base_url}/public/message/"
		headers = {
			"Authorization": f"Basic {self.api_key}",
			"Content-Type": "application/json",
		}

		try:
			response = requests.post(url, json=payload, headers=headers, timeout=30)
			response.raise_for_status()
			
			result = response.json()
			
			if result.get("result"):
				return {
					"success": True,
					"message_id": result.get("id"),
					"message": result.get("message", "Message sent successfully"),
				}
			else:
				return {
					"success": False,
					"error": result.get("message", "Failed to send message"),
				}
				
		except requests.exceptions.RequestException as e:
			frappe.log_error(
				title="Interakt API Error",
				message=f"Error sending message: {str(e)}\nPayload: {payload}",
			)
			return {
				"success": False,
				"error": str(e),
			}

	def track_user(
		self,
		phone_number,
		country_code=None,
		user_id=None,
		traits=None,
		created_at=None,
	):
		"""
		Track user in Interakt (User Track API).
		
		:param phone_number: Phone number without country code
		:param country_code: Country code
		:param user_id: Unique user identifier
		:param traits: Dict of user attributes (name, email, etc.)
		:param created_at: ISO-8601 timestamp
		:return: Response dict
		"""
		if not self.api_key:
			frappe.throw(_("Interakt API Key is not configured"))

		# Clean phone number
		phone_number = "".join(filter(str.isdigit, str(phone_number)))
		country_code = country_code or self.default_country_code

		payload = {
			"phoneNumber": phone_number,
			"countryCode": country_code,
		}

		if user_id:
			payload["userId"] = user_id

		if traits:
			payload["traits"] = traits

		if created_at:
			payload["createdAt"] = created_at

		# Make API request
		url = f"{self.base_url}/public/track/users/"
		headers = {
			"Authorization": f"Basic {self.api_key}",
			"Content-Type": "application/json",
		}

		try:
			response = requests.post(url, json=payload, headers=headers, timeout=30)
			response.raise_for_status()
			return {"success": True, "data": response.json()}
		except requests.exceptions.RequestException as e:
			frappe.log_error(
				title="Interakt User Track Error",
				message=f"Error tracking user: {str(e)}\nPayload: {payload}",
			)
			return {"success": False, "error": str(e)}

	def track_event(
		self,
		phone_number,
		country_code=None,
		user_id=None,
		event=None,
		traits=None,
		created_at=None,
	):
		"""
		Track event in Interakt (Event Track API).
		
		:param phone_number: Phone number without country code
		:param country_code: Country code
		:param user_id: Unique user identifier
		:param event: Event name (e.g., 'OrderPlaced', 'LeadCreated')
		:param traits: Dict of event properties
		:param created_at: ISO-8601 timestamp
		:return: Response dict
		"""
		if not self.api_key:
			frappe.throw(_("Interakt API Key is not configured"))

		# Clean phone number
		phone_number = "".join(filter(str.isdigit, str(phone_number)))
		country_code = country_code or self.default_country_code

		payload = {
			"phoneNumber": phone_number,
			"countryCode": country_code,
		}

		if user_id:
			payload["userId"] = user_id

		if event:
			payload["event"] = event

		if traits:
			payload["traits"] = traits

		if created_at:
			payload["createdAt"] = created_at

		# Make API request
		url = f"{self.base_url}/public/track/events/"
		headers = {
			"Authorization": f"Basic {self.api_key}",
			"Content-Type": "application/json",
		}

		try:
			response = requests.post(url, json=payload, headers=headers, timeout=30)
			response.raise_for_status()
			return {"success": True, "data": response.json()}
		except requests.exceptions.RequestException as e:
			frappe.log_error(
				title="Interakt Event Track Error",
				message=f"Error tracking event: {str(e)}\nPayload: {payload}",
			)
			return {"success": False, "error": str(e)}

	def send_text_message(
		self,
		phone_number,
		message_text,
		user_id=None,
		callback_data=None,
	):
		"""
		Send a free text WhatsApp message via Interakt API.
		
		:param phone_number: Full phone number with country code (e.g., +919876543210)
		:param message_text: The text message to send
		:param user_id: Optional user identifier
		:param callback_data: Optional callback data
		:return: Response dict with message_id
		"""
		if not self.api_key:
			frappe.throw(_("Interakt API Key is not configured"))

		# Prepare request payload
		# Clean phone number (keep + and digits)
		phone_number = "".join(c for c in str(phone_number) if c.isdigit() or c == '+')

		payload = {
			"fullPhoneNumber": phone_number,
			"type": "Text",
			"data": {
				"message": message_text
			}
		}

		# Add optional fields
		if user_id:
			payload["userId"] = user_id

		if callback_data:
			payload["callbackData"] = callback_data

		# Make API request
		url = f"{self.base_url}/public/message/"
		headers = {
			"Authorization": f"Basic {self.api_key}",
			"Content-Type": "application/json",
		}

		try:
			frappe.logger().info(f"Sending text message to Interakt API. URL: {url}")
			frappe.logger().info(f"Payload: {payload}")
			
			response = requests.post(url, json=payload, headers=headers, timeout=30)
			
			# Log the response for debugging
			frappe.logger().info(f"Interakt API Response Status: {response.status_code}")
			frappe.logger().info(f"Interakt API Response Body: {response.text}")
			
			response.raise_for_status()
			
			result = response.json()
			
			if result.get("result"):
				return {
					"success": True,
					"message_id": result.get("id"),
					"message": result.get("message", "Message sent successfully"),
				}
			else:
				return {
					"success": False,
					"error": result.get("message", "Failed to send message"),
				}
				
		except requests.exceptions.RequestException as e:
			error_details = str(e)
			response_text = ""
			error_message = str(e)
			
			if hasattr(e, 'response') and e.response is not None:
				response_text = e.response.text
				error_details = f"{str(e)}\nResponse: {response_text}"
				
				# Check if it's a 400 error related to 24-hour window
				if e.response.status_code == 400:
					try:
						response_json = e.response.json()
						api_error_msg = response_json.get("message", "").lower()
						
						# Common error messages for 24-hour window violations
						if any(keyword in api_error_msg for keyword in ["24 hour", "conversation window", "session", "template required"]):
							error_message = (
								"Cannot send free text message: The 24-hour conversation window has expired. "
								"Free text messages can only be sent within 24 hours after the customer's last message. "
								"Please use a WhatsApp template message instead."
							)
						else:
							error_message = f"Interakt API Error: {response_json.get('message', str(e))}"
					except:
						error_message = f"Interakt API Error (400 Bad Request): {response_text}"
			
			frappe.log_error(
				title="Interakt Text Message Error",
				message=f"Error sending text message: {error_details}\nPayload: {payload}",
			)
			return {
				"success": False,
				"error": error_message,
			}

	def get_templates(self, offset=0, autosubmitted_for="all", language="all"):
		"""
		Fetch all WhatsApp templates from Interakt.
		
		:param offset: Pagination offset (default: 0)
		:param autosubmitted_for: Filter for autosubmitted templates (default: "all")
		:param language: Language filter (default: "all")
		:return: Dict with success status and templates list
		"""
		if not self.api_key:
			frappe.throw(_("Interakt API Key is not configured"))

		# Make API request with GET method and query parameters
		url = f"{self.base_url}/public/track/organization/templates"
		headers = {
			"Authorization": f"Basic {self.api_key}",
			"Content-Type": "application/json",
		}
		
		# Pass parameters as query params
		params = {
			"offset": offset,
			"autosubmitted_for": autosubmitted_for,
			"language": language,
		}

		try:
			frappe.logger().info(f"Fetching templates from Interakt API. URL: {url}")
			frappe.logger().info(f"Query Params: {params}")
			
			# Use GET request with params, not POST with json
			response = requests.get(url, params=params, headers=headers, timeout=30)
			
			# Log the response for debugging
			frappe.logger().info(f"Interakt API Response Status: {response.status_code}")
			frappe.logger().info(f"Interakt API Response Body: {response.text}")
			
			response.raise_for_status()
			
			result = response.json()
			
			# Interakt API returns templates in different formats
			# Handle both possible response structures
			if isinstance(result, dict):
				if "data" in result:
					templates = result.get("data", [])
				elif "templates" in result:
					templates = result.get("templates", [])
				else:
					# If result itself contains template data
					templates = [result] if result else []
			elif isinstance(result, list):
				templates = result
			else:
				templates = []
			
			return {
				"success": True,
				"templates": templates,
				"count": len(templates),
			}
			
		except requests.exceptions.RequestException as e:
			error_details = str(e)
			response_text = ""
			
			if hasattr(e, 'response') and e.response is not None:
				response_text = e.response.text
				error_details = f"{str(e)}\nResponse: {response_text}"
			
			frappe.log_error(
				title="Interakt Get Templates Error",
				message=f"Error fetching templates: {error_details}\nQuery Params: {params}",
			)
			return {
				"success": False,
				"error": str(e),
				"templates": [],
			}
