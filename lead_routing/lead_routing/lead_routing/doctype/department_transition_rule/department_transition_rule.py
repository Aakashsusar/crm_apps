# Copyright (c) 2026, IP CRM and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class DepartmentTransitionRule(Document):
	def validate(self):
		if self.from_stage == self.to_stage:
			frappe.throw(_("From Stage and To Stage cannot be the same"))

		# Check for duplicate rules
		existing = frappe.db.exists(
			"Department Transition Rule",
			{
				"from_stage": self.from_stage,
				"to_stage": self.to_stage,
				"name": ("!=", self.name),
			},
		)
		if existing:
			frappe.throw(
				_("A transition rule from {0} to {1} already exists").format(
					self.from_stage, self.to_stage
				)
			)
