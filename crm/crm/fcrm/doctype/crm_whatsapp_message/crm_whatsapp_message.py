# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class CRMWhatsAppMessage(Document):
	def after_insert(self):
		"""Publish realtime event after message is created."""
		
		# Prepare message data for frontend
		message_data = self.as_dict()
		message_data.update({
			"type": self.direction, 
			"message": self.message_content, 
			"from_name": "You" if self.direction == "Outgoing" else "Client", 
			# Critical fields for frontend rendering
			"content_type": "text" if not self.media_url else "image", 
			"message_type": "Text", # Simplified
			"status": self.status.lower(),
			"creation": frappe.utils.now(), # Ensure creation is available immediately
		})
		
		# Try to improve from_name
		if self.direction == "Incoming":
			# Try to get customer name from reference doc if possible, but keeping it simple for now as it's async
			pass
			
		frappe.publish_realtime(
			"whatsapp_message",
			{
				"message_id": self.message_id,
				"reference_doctype": self.reference_doctype,
				# Frontend expects reference_name
				"reference_name": self.reference_docname,
				"status": self.status,
				"message_data": message_data,
			},
			after_commit=True,
		)
