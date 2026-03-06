# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import get_url


class CRMInteraktSettings(Document):
	def before_save(self):
		self.set_webhook_url()

	def set_webhook_url(self):
		"""Set the webhook URL for Interakt."""
		if self.enabled:
			webhook_path = "/api/method/crm.integrations.interakt.webhooks.handle_webhook"
			self.webhook_url = get_url(webhook_path)
