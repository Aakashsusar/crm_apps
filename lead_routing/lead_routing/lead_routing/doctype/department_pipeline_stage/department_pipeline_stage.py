# Copyright (c) 2026, IP CRM and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class DepartmentPipelineStage(Document):
	def validate(self):
		if self.stage_order < 1:
			frappe.throw(_("Stage Order must be a positive integer"))

		if self.is_terminal and self.stage_order != self._get_max_order():
			# Terminal stage should be the last one, but we allow it anywhere
			pass

	def _get_max_order(self):
		result = frappe.db.sql(
			"SELECT MAX(stage_order) FROM `tabDepartment Pipeline Stage` WHERE name != %s",
			self.name,
		)
		return (result[0][0] or 0) if result else 0

	def get_internal_status_list(self):
		"""Return the internal statuses as a list."""
		if not self.internal_statuses:
			return []
		return [s.strip() for s in self.internal_statuses.split(",") if s.strip()]
