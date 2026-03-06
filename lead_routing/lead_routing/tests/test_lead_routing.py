# Copyright (c) 2026, IP CRM and contributors
# For license information, please see license.txt

"""
Test suite for the Department-Based Lead Routing System.

Covers:
- Shift detection logic
- Forward transitions (mark_department_done)
- Backward transitions (send_back_to_department)
- Reject transitions (reject_to_onboarding)
- Manager override transfers
- Invalid transition prevention
- Shift persistence across transfers
- Terminal stage completion
- Data integrity safeguards
"""

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import now_datetime, get_datetime
from datetime import datetime, time, timedelta


class TestLeadRouting(FrappeTestCase):
	"""Test department-based lead routing pipeline."""

	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		cls._ensure_setup_data()

	@classmethod
	def _ensure_setup_data(cls):
		"""Ensure pipeline stages, shifts, and transition rules exist."""
		if not frappe.db.exists("Department Pipeline Stage", "Seller Onboarding"):
			from lead_routing.setup import run_setup
			run_setup()

	def _create_test_lead(self, shift_time=None):
		"""Create a test CRM Lead and return it."""
		lead = frappe.new_doc("CRM Lead")
		lead.first_name = f"Test-{frappe.generate_hash(length=6)}"
		lead.last_name = "Lead"
		lead.status = "New"

		if not frappe.db.exists("CRM Lead Status", "New"):
			status = frappe.new_doc("CRM Lead Status")
			status.lead_status = "New"
			status.insert(ignore_permissions=True)

		lead.insert(ignore_permissions=True)
		lead.reload()
		return lead

	# ─────────────────────────────────────────────────────────────
	# SHIFT DETECTION TESTS
	# ─────────────────────────────────────────────────────────────

	def test_shift_detection_morning(self):
		"""Lead created during morning hours should be assigned Morning Shift."""
		from lead_routing.api.lead_transfer import _get_shift_for_time

		# 10 AM — should be Morning Shift (06:00-18:00)
		morning_dt = datetime(2026, 2, 23, 10, 0, 0)
		shift = _get_shift_for_time(morning_dt)
		self.assertIsNotNone(shift)
		self.assertEqual(shift.name, "Morning Shift")

	def test_shift_detection_night(self):
		"""Lead created during night hours should be assigned Night Shift."""
		from lead_routing.api.lead_transfer import _get_shift_for_time

		# 11 PM — should be Night Shift (18:00-06:00)
		night_dt = datetime(2026, 2, 23, 23, 0, 0)
		shift = _get_shift_for_time(night_dt)
		self.assertIsNotNone(shift)
		self.assertEqual(shift.name, "Night Shift")

	def test_shift_detection_boundary(self):
		"""Lead created at exact boundary should be in correct shift."""
		from lead_routing.api.lead_transfer import _get_shift_for_time

		# Exactly 18:00 — should be Night Shift (start inclusive)
		boundary_dt = datetime(2026, 2, 23, 18, 0, 0)
		shift = _get_shift_for_time(boundary_dt)
		self.assertIsNotNone(shift)
		self.assertEqual(shift.name, "Night Shift")

	def test_shift_detection_early_morning(self):
		"""Lead created at 3 AM (early morning) should be Night Shift."""
		from lead_routing.api.lead_transfer import _get_shift_for_time

		early_dt = datetime(2026, 2, 23, 3, 0, 0)
		shift = _get_shift_for_time(early_dt)
		self.assertIsNotNone(shift)
		self.assertEqual(shift.name, "Night Shift")

	# ─────────────────────────────────────────────────────────────
	# INITIAL ASSIGNMENT TESTS
	# ─────────────────────────────────────────────────────────────

	def test_lead_initial_assignment(self):
		"""New lead should be assigned to the first department."""
		lead = self._create_test_lead()

		self.assertEqual(lead.current_department, "Seller Onboarding")
		self.assertIn(lead.current_shift, ["Morning Shift", "Night Shift"])
		self.assertEqual(lead.department_status, "Working")

	def test_lead_has_initial_history(self):
		"""New lead should have one department history entry."""
		lead = self._create_test_lead()

		self.assertEqual(len(lead.department_history), 1)
		self.assertEqual(lead.department_history[0].department, "Seller Onboarding")
		self.assertEqual(lead.department_history[0].action, "Initial")
		self.assertIsNotNone(lead.department_history[0].entered_at)
		self.assertIsNone(lead.department_history[0].exited_at)

	# ─────────────────────────────────────────────────────────────
	# FORWARD TRANSITION TESTS
	# ─────────────────────────────────────────────────────────────

	def test_forward_transition(self):
		"""mark_department_done should move lead to the next stage."""
		from lead_routing.api.lead_transfer import mark_department_done

		lead = self._create_test_lead()
		self.assertEqual(lead.current_department, "Seller Onboarding")

		# Give user the required role
		self._add_role_to_user("Seller Onboarding User")

		result = mark_department_done(lead.name)
		lead.reload()

		self.assertEqual(result["status"], "transferred")
		self.assertEqual(lead.current_department, "Product Listing")
		self.assertEqual(lead.department_status, "Working")

	def test_forward_chain(self):
		"""Lead should flow through all departments: SO → PL → GA → AM → Completion."""
		from lead_routing.api.lead_transfer import mark_department_done

		lead = self._create_test_lead()
		original_shift = lead.current_shift

		expected_stages = [
			("Seller Onboarding", "Product Listing"),
			("Product Listing", "Google Ads"),
			("Google Ads", "Account Manager"),
			("Account Manager", "Completion"),
		]

		for from_stage, to_stage in expected_stages:
			self._add_role_to_user(f"{from_stage} User")
			result = mark_department_done(lead.name)
			lead.reload()

			self.assertEqual(result["to"], to_stage)
			self.assertEqual(lead.current_department, to_stage)
			# Shift should remain the same throughout
			self.assertEqual(lead.current_shift, original_shift)

	def test_terminal_stage_completion(self):
		"""Marking done at Completion stage should end the lifecycle."""
		from lead_routing.api.lead_transfer import mark_department_done

		lead = self._create_test_lead()

		# Move lead through all stages to Completion
		stages = ["Seller Onboarding", "Product Listing", "Google Ads", "Account Manager"]
		for stage in stages:
			self._add_role_to_user(f"{stage} User")
			mark_department_done(lead.name)

		lead.reload()
		self.assertEqual(lead.current_department, "Completion")

		# Now mark done at Completion
		self._add_role_to_user("Completion User")
		result = mark_department_done(lead.name)
		lead.reload()

		self.assertEqual(result["status"], "completed")
		self.assertEqual(lead.department_status, "Done")

	# ─────────────────────────────────────────────────────────────
	# BACKWARD TRANSITION TESTS
	# ─────────────────────────────────────────────────────────────

	def test_backward_transition_google_ads_to_product_listing(self):
		"""Google Ads can send lead back to Product Listing."""
		from lead_routing.api.lead_transfer import mark_department_done, send_back_to_department

		lead = self._create_test_lead()

		# Move to Google Ads
		self._add_role_to_user("Seller Onboarding User")
		mark_department_done(lead.name)
		self._add_role_to_user("Product Listing User")
		mark_department_done(lead.name)
		lead.reload()
		self.assertEqual(lead.current_department, "Google Ads")

		# Send back to Product Listing
		self._add_role_to_user("Google Ads User")
		result = send_back_to_department(lead.name, "Product Listing")
		lead.reload()

		self.assertEqual(result["status"], "sent_back")
		self.assertEqual(lead.current_department, "Product Listing")

	def test_backward_transition_account_manager_to_product_listing(self):
		"""Account Manager can send lead back to Product Listing."""
		from lead_routing.api.lead_transfer import mark_department_done, send_back_to_department

		lead = self._create_test_lead()

		# Move to Account Manager (through all stages)
		for stage in ["Seller Onboarding", "Product Listing", "Google Ads"]:
			self._add_role_to_user(f"{stage} User")
			mark_department_done(lead.name)

		lead.reload()
		self.assertEqual(lead.current_department, "Account Manager")

		# Send back
		self._add_role_to_user("Account Manager User")
		result = send_back_to_department(lead.name, "Product Listing")
		lead.reload()

		self.assertEqual(lead.current_department, "Product Listing")

	def test_backward_then_forward_resumes(self):
		"""After backward, lead should continue forward from the backward target."""
		from lead_routing.api.lead_transfer import mark_department_done, send_back_to_department

		lead = self._create_test_lead()

		# Move to Google Ads
		self._add_role_to_user("Seller Onboarding User")
		mark_department_done(lead.name)
		self._add_role_to_user("Product Listing User")
		mark_department_done(lead.name)

		# Send back to Product Listing
		self._add_role_to_user("Google Ads User")
		send_back_to_department(lead.name, "Product Listing")

		# Now move forward again — should go back to Google Ads
		self._add_role_to_user("Product Listing User")
		result = mark_department_done(lead.name)
		lead.reload()

		self.assertEqual(lead.current_department, "Google Ads")

	# ─────────────────────────────────────────────────────────────
	# REJECT TRANSITION TESTS
	# ─────────────────────────────────────────────────────────────

	def test_reject_to_onboarding(self):
		"""Any department can reject lead back to Seller Onboarding."""
		from lead_routing.api.lead_transfer import mark_department_done, reject_to_onboarding

		lead = self._create_test_lead()

		# Move to Google Ads
		self._add_role_to_user("Seller Onboarding User")
		mark_department_done(lead.name)
		self._add_role_to_user("Product Listing User")
		mark_department_done(lead.name)

		# Reject from Google Ads
		self._add_role_to_user("Google Ads User")
		result = reject_to_onboarding(lead.name)
		lead.reload()

		self.assertEqual(result["status"], "rejected")
		self.assertEqual(lead.current_department, "Seller Onboarding")

	def test_reject_from_first_stage_fails(self):
		"""Rejecting from the first stage should fail."""
		from lead_routing.api.lead_transfer import reject_to_onboarding

		lead = self._create_test_lead()
		self._add_role_to_user("Seller Onboarding User")

		with self.assertRaises(frappe.ValidationError):
			reject_to_onboarding(lead.name)

	# ─────────────────────────────────────────────────────────────
	# INVALID TRANSITION TESTS
	# ─────────────────────────────────────────────────────────────

	def test_skip_stage_fails(self):
		"""Cannot send lead to a non-adjacent stage via send_back."""
		from lead_routing.api.lead_transfer import send_back_to_department, mark_department_done

		lead = self._create_test_lead()

		# Move to Google Ads
		self._add_role_to_user("Seller Onboarding User")
		mark_department_done(lead.name)
		self._add_role_to_user("Product Listing User")
		mark_department_done(lead.name)

		# Try to send back to Seller Onboarding via backward (not reject) — no rule for this
		self._add_role_to_user("Google Ads User")
		with self.assertRaises(frappe.ValidationError):
			send_back_to_department(lead.name, "Seller Onboarding")

	# ─────────────────────────────────────────────────────────────
	# MANAGER OVERRIDE TESTS
	# ─────────────────────────────────────────────────────────────

	def test_manager_override(self):
		"""Manager can transfer lead to any department."""
		from lead_routing.api.lead_transfer import manager_override_transfer

		lead = self._create_test_lead()
		self._add_role_to_user("Seller Onboarding Manager")

		result = manager_override_transfer(lead.name, "Google Ads", "Client requested fast-track")
		lead.reload()

		self.assertEqual(result["status"], "override_transferred")
		self.assertEqual(lead.current_department, "Google Ads")

	# ─────────────────────────────────────────────────────────────
	# SHIFT PERSISTENCE TESTS
	# ─────────────────────────────────────────────────────────────

	def test_shift_persist_across_transfers(self):
		"""Shift should not change when lead moves between departments."""
		from lead_routing.api.lead_transfer import mark_department_done

		lead = self._create_test_lead()
		original_shift = lead.current_shift

		self._add_role_to_user("Seller Onboarding User")
		mark_department_done(lead.name)
		lead.reload()

		self.assertEqual(lead.current_shift, original_shift)

	# ─────────────────────────────────────────────────────────────
	# HISTORY TRACKING TESTS
	# ─────────────────────────────────────────────────────────────

	def test_department_history_grows(self):
		"""Each transition should add a history entry."""
		from lead_routing.api.lead_transfer import mark_department_done

		lead = self._create_test_lead()
		initial_count = len(lead.department_history)

		self._add_role_to_user("Seller Onboarding User")
		mark_department_done(lead.name)
		lead.reload()

		self.assertEqual(len(lead.department_history), initial_count + 1)

	def test_history_entry_exit_timestamps(self):
		"""Previous department's log entry should have exited_at set after transfer."""
		from lead_routing.api.lead_transfer import mark_department_done

		lead = self._create_test_lead()

		self._add_role_to_user("Seller Onboarding User")
		mark_department_done(lead.name)
		lead.reload()

		# First entry (Seller Onboarding) should have exited_at
		first_entry = lead.department_history[0]
		self.assertIsNotNone(first_entry.exited_at)

		# Second entry (Product Listing) should NOT have exited_at
		second_entry = lead.department_history[1]
		self.assertIsNone(second_entry.exited_at)

	# ─────────────────────────────────────────────────────────────
	# DATA INTEGRITY TESTS
	# ─────────────────────────────────────────────────────────────

	def test_prevent_manual_department_change(self):
		"""Direct assignment of current_department should be blocked."""
		lead = self._create_test_lead()

		lead.current_department = "Google Ads"
		with self.assertRaises(frappe.ValidationError):
			lead.save()

	# ─────────────────────────────────────────────────────────────
	# HELPER METHODS
	# ─────────────────────────────────────────────────────────────

	def _add_role_to_user(self, role_name):
		"""Temporarily add a role to the current test user (Administrator)."""
		user = frappe.get_doc("User", frappe.session.user)
		existing_roles = [r.role for r in user.roles]
		if role_name not in existing_roles:
			user.append("roles", {"role": role_name})
			user.save(ignore_permissions=True)
