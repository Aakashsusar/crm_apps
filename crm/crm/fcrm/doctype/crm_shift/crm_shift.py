import frappe
from frappe.model.document import Document
from datetime import datetime, time


class CRMShift(Document):
	"""CRM Shift Master"""
	
	def validate(self):
		"""Validate shift timing"""
		if self.start_time and self.end_time:
			# Convert to time objects for comparison
			start = datetime.strptime(str(self.start_time), "%H:%M:%S").time()
			end = datetime.strptime(str(self.end_time), "%H:%M:%S").time()
			
			# Allow overnight shifts (end < start means shift crosses midnight)
			if start == end:
				frappe.throw("Start time and end time cannot be the same")
	
	def is_active_now(self):
		"""Check if shift is currently active"""
		now = datetime.now()
		current_time = now.time()
		current_day = now.strftime("%A").lower()
		
		# Check if today is an active day
		if not getattr(self, current_day, 0):
			return False
		
		# Check if current time is within shift hours
		start = datetime.strptime(str(self.start_time), "%H:%M:%S").time()
		end = datetime.strptime(str(self.end_time), "%H:%M:%S").time()
		
		# Handle overnight shifts
		if end < start:
			# Shift crosses midnight
			return current_time >= start or current_time <= end
		else:
			# Normal shift
			return start <= current_time <= end
	
	def get_remaining_time(self):
		"""Get remaining time in shift (in minutes)"""
		if not self.is_active_now():
			return 0
		
		now = datetime.now()
		current_time = now.time()
		end = datetime.strptime(str(self.end_time), "%H:%M:%S").time()
		
		# Calculate remaining minutes
		end_datetime = datetime.combine(now.date(), end)
		current_datetime = datetime.combine(now.date(), current_time)
		
		# Handle overnight shifts
		if end < current_time:
			# Shift ends tomorrow
			from datetime import timedelta
			end_datetime = end_datetime + timedelta(days=1)
		
		remaining = (end_datetime - current_datetime).total_seconds() / 60
		return max(0, int(remaining))


@frappe.whitelist()
def get_active_shifts():
	"""Get all currently active shifts"""
	shifts = frappe.get_all(
		"CRM Shift",
		filters={"enabled": 1},
		fields=["name", "shift_name", "start_time", "end_time"]
	)
	
	active_shifts = []
	for shift_data in shifts:
		shift = frappe.get_doc("CRM Shift", shift_data.name)
		if shift.is_active_now():
			active_shifts.append({
				"name": shift.name,
				"shift_name": shift.shift_name,
				"start_time": str(shift.start_time),
				"end_time": str(shift.end_time),
				"remaining_minutes": shift.get_remaining_time()
			})
	
	return active_shifts


@frappe.whitelist()
def check_shift_active(shift_name):
	"""Check if a specific shift is currently active"""
	if not shift_name:
		return {"active": False, "message": "No shift specified"}
	
	shift = frappe.get_doc("CRM Shift", shift_name)
	is_active = shift.is_active_now()
	
	return {
		"active": is_active,
		"shift_name": shift.shift_name,
		"remaining_minutes": shift.get_remaining_time() if is_active else 0,
		"start_time": str(shift.start_time),
		"end_time": str(shift.end_time)
	}
