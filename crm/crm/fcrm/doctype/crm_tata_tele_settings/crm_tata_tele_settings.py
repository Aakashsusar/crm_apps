import frappe
from frappe.model.document import Document


class CRMTataTeleSettings(Document):
	"""Tata Teleservices integration settings"""
	pass


class TataTeleSettings:
	"""Helper class for Tata Teleservices settings"""

	@staticmethod
	def is_enabled():
		"""Check if Tata Tele integration is enabled"""
		return frappe.db.get_single_value("CRM Tata Tele Settings", "enabled")

	@staticmethod
	def get_settings():
		"""Get Tata Tele settings"""
		if not TataTeleSettings.is_enabled():
			return None

		return frappe.get_single("CRM Tata Tele Settings")

	@staticmethod
	def get_api_endpoint():
		"""Get API endpoint"""
		settings = TataTeleSettings.get_settings()
		return settings.api_endpoint if settings else None

	@staticmethod
	def get_api_token():
		"""Get API token"""
		settings = TataTeleSettings.get_settings()
		return settings.get_password("api_token") if settings else None

	@staticmethod
	def get_webhook_token():
		"""Get Webhook token"""
		settings = TataTeleSettings.get_settings()
		return settings.get_password("webhook_token") if settings else None

	@staticmethod
	def get_agent_number():
		"""Get agent number (virtual number from Tata system)"""
		settings = TataTeleSettings.get_settings()
		return settings.agent_number if settings else None

	@staticmethod
	def get_caller_id():
		"""Get caller ID (number that appears on recipient's phone)"""
		settings = TataTeleSettings.get_settings()
		return settings.caller_id if settings else None

	@staticmethod
	def get_account_id():
		"""Get account ID"""
		settings = TataTeleSettings.get_settings()
		return settings.account_id if settings else None

	@staticmethod
	def get_account_id():
		"""Get Account ID"""
		settings = TataTeleSettings.get_settings()
		return settings.account_id if settings else None

	@staticmethod
	def get_phone_number():
		"""Get default phone number"""
		settings = TataTeleSettings.get_settings()
		return settings.phone_number if settings else None
