import frappe
from frappe.model.document import Document


class SmartfloAgentMapping(Document):
    def validate(self):
        # Fetch user name automatically
        if self.user:
            user_doc = frappe.get_doc("User", self.user)
            self.user_name = user_doc.full_name