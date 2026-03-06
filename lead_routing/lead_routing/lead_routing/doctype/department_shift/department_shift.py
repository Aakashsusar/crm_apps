# Copyright (c) 2026, IP CRM and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class DepartmentShift(Document):
	def validate(self):
		if not self.start_time or not self.end_time:
			frappe.throw(_("Both Start Time and End Time are required"))
