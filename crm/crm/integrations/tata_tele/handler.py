# apps/crm/crm/integrations/tata_tele/handler.py

import uuid
import json
import frappe
import requests
from frappe import _

from crm.integrations.api import get_contact_by_phone_number
from crm.fcrm.doctype.crm_tata_tele_settings.crm_tata_tele_settings import TataTeleSettings


# =========================================================
# Helpers
# =========================================================

def is_integration_enabled():
	return TataTeleSettings.is_enabled()


def _get_json():
	try:
		return frappe.request.get_json(silent=True) or {}
	except Exception:
		raw = frappe.request.get_data(as_text=True) or "{}"
		try:
			return json.loads(raw)
		except Exception:
			return {}


def _pick(d, keys):
	if not isinstance(d, dict):
		return None
	for k in keys:
		v = d.get(k)
		if v not in (None, ""):
			return v
	return None


def _norm_num(v):
	"""Keep only digits and +"""
	if not v:
		return None
	s = str(v).strip()
	out = []
	for ch in s:
		if ch.isdigit() or ch == "+":
			out.append(ch)
	return "".join(out) or None


def _only_last_10(v):
	"""
	Convert +919359889256 / 919359889256 / 9359889256 -> 9359889256
	Always store ONLY last 10 digits in DB.
	"""
	n = _norm_num(v)
	if not n:
		return None
	d = "".join(ch for ch in n if ch.isdigit())
	if len(d) >= 10:
		return d[-10:]
	return d or None


def _parse_dt(v):
	if not v:
		return None
	try:
		return frappe.utils.get_datetime(str(v).strip())
	except Exception:
		return None


def _extract_ref_id(payload):
	return _pick(payload, ["ref_id", "refId", "refID"])


def _extract_call_id(payload):
	return _pick(payload, ["call_id", "callId", "callid"])


def _extract_customer(payload):
	# Outbound "customer" = destination number
	return _only_last_10(_pick(payload, [
		"customer_no_with_prefix", "customer_no_with_prefix ",
		"customer_number_with_prefix", "customer_number_with_prefix ",
		"customer_number",
		"call_to_number",
		"destination_number",
	]))


def _extract_agent(payload):
	# Agent who answered / caller id
	return _only_last_10(_pick(payload, [
		"answer_agent_number",        # ✅ NEW: from answered webhook
		"answered_agent_number",
		"answer_agent_number",
		"caller_id_number",
		"agent_number",
	]))


def _extract_duration(payload):
	# prefer billsec first (talktime)
	v = _pick(payload, ["billsec", "duration"])
	if v in (None, ""):
		return None
	try:
		return float(v)
	except Exception:
		return None


def _extract_start(payload):
	return _parse_dt(_pick(payload, ["start_stamp"]))


def _extract_answer(payload):
	return _parse_dt(_pick(payload, ["answer_stamp"]))


def _extract_end(payload):
	return _parse_dt(_pick(payload, ["end_stamp"]))


def _extract_recording(payload):
	v = _pick(payload, ["recording_url"])
	return str(v).strip()[:140] if v else None


def _extract_hangup_cause(payload):
	"""Extract hangup cause/reason from webhook"""
	return _pick(payload, [
		"hangup_cause_description",
		"hangupcause_desc",
		"reason_key",
		"hangup_cause_key"
	])


def _extract_call_connected(payload):
	"""Check if call was successfully connected"""
	val = payload.get("call_connected")
	if isinstance(val, str):
		return val.strip().lower() in ("1", "true", "yes")
	return bool(val) if val is not None else None


def _extract_answered_agent(payload):
	"""Get the agent who answered the call"""
	# answered_agent can be a dict with 'name' or 'agent_number'
	answered_agent = payload.get("answered_agent")
	if isinstance(answered_agent, dict):
		return answered_agent.get("name") or answered_agent.get("agent_number")
	# Or it can be a string
	return _pick(payload, ["answered_agent", "answered_agent_name"])


def _extract_missed_agent(payload):
	"""Get the agent who missed the call"""
	return _pick(payload, ["missed_agent"])


def _to_int(x):
	try:
		return int(float(str(x).strip()))
	except Exception:
		return 0


def _map_status(payload):
	"""
	Robust status mapping for Smartflow outbound webhooks.

	Uses multiple indicators to determine final status:
	- answered_agent: agent who answered
	- missed_agent: agent who missed
	- call_connected: boolean for successful connection
	- billsec/duration: actual talk time
	- hangup_cause: reason for call end
	- end_stamp: call ended timestamp
	"""
	call_status = (payload.get("call_status") or "").strip().lower()

	end_dt = _extract_end(payload)
	answer_dt = _extract_answer(payload)

	billsec = _to_int(_pick(payload, ["billsec"]) or 0)
	duration = _to_int(_pick(payload, ["duration"]) or 0)

	# NEW: Extract additional indicators
	call_connected = _extract_call_connected(payload)
	answered_agent = _extract_answered_agent(payload)
	missed_agent = _extract_missed_agent(payload)
	hangup_cause = _extract_hangup_cause(payload)

	# Debug logging
	frappe.logger().info(
		f"[SMARTFLOW STATUS MAPPING] call_status='{call_status}', "
		f"end_dt={end_dt}, answer_dt={answer_dt}, billsec={billsec}, duration={duration}, "
		f"call_connected={call_connected}, answered_agent='{answered_agent}', "
		f"missed_agent='{missed_agent}', hangup_cause='{hangup_cause}'"
	)

	# Provider statuses for in-progress calls
	if call_status in ("ringing", "agent_ringing"):
		frappe.logger().info("[SMARTFLOW STATUS MAPPING] Returning: Ringing")
		return "Ringing"

	if call_status in ("answered", "connected", "in_progress", "active"):
		frappe.logger().info("[SMARTFLOW STATUS MAPPING] Returning: In Progress")
		return "In Progress"

	# Explicit provider status for completed
	if call_status in ("completed", "hangup", "ended", "disconnected"):
		# Check if call was actually answered and connected
		if answered_agent and (answer_dt or call_connected or billsec > 0):
			frappe.logger().info("[SMARTFLOW STATUS MAPPING] Returning: Completed (answered with agent)")
			return "Completed"
		
		# Check if explicitly missed
		if missed_agent:
			frappe.logger().info("[SMARTFLOW STATUS MAPPING] Returning: No answer (missed agent)")
			return "No answer"
		
		# No answer/duration = not answered
		frappe.logger().info("[SMARTFLOW STATUS MAPPING] Returning: No answer (ended without answer)")
		return "No answer"

	# Explicit no answer statuses
	if call_status in ("no_answer", "missed", "not_answered"):
		frappe.logger().info("[SMARTFLOW STATUS MAPPING] Returning: No answer")
		return "No answer"

	if call_status in ("failed",):
		frappe.logger().info("[SMARTFLOW STATUS MAPPING] Returning: Failed")
		return "Failed"

	if call_status in ("busy",):
		frappe.logger().info("[SMARTFLOW STATUS MAPPING] Returning: Busy")
		return "Busy"

	if call_status in ("cancelled", "canceled"):
		frappe.logger().info("[SMARTFLOW STATUS MAPPING] Returning: Cancelled")
		return "Cancelled"

	# FINAL heuristic when call has ended
	if end_dt:
		# Check hangup cause for specific reasons
		if hangup_cause:
			cause_lower = str(hangup_cause).lower()
			if "cancel" in cause_lower or "user" in cause_lower:
				frappe.logger().info(f"[SMARTFLOW STATUS MAPPING] Returning: Cancelled (hangup_cause: {hangup_cause})")
				return "Cancelled"
			if "busy" in cause_lower:
				frappe.logger().info(f"[SMARTFLOW STATUS MAPPING] Returning: Busy (hangup_cause: {hangup_cause})")
				return "Busy"
			if "no answer" in cause_lower or "missed" in cause_lower or "timeout" in cause_lower:
				frappe.logger().info(f"[SMARTFLOW STATUS MAPPING] Returning: No answer (hangup_cause: {hangup_cause})")
				return "No answer"
		
		# Check if answered with duration
		if answered_agent and (answer_dt or call_connected or billsec > 0 or duration > 0):
			frappe.logger().info("[SMARTFLOW STATUS MAPPING] Returning: Completed (heuristic - answered with duration)")
			return "Completed"
		
		# Check if missed
		if missed_agent:
			frappe.logger().info("[SMARTFLOW STATUS MAPPING] Returning: No answer (heuristic - missed)")
			return "No answer"
		
		# Has duration but no answered_agent = still completed
		if billsec > 0 or duration > 0:
			frappe.logger().info("[SMARTFLOW STATUS MAPPING] Returning: Completed (heuristic - has duration)")
			return "Completed"
		
		# Ended without answer
		frappe.logger().info("[SMARTFLOW STATUS MAPPING] Returning: No answer (heuristic - ended without answer/duration)")
		return "No answer"

	# Call in progress if agent answered
	if payload.get("answered_agent_number") or payload.get("answer_agent_number") or answered_agent:
		frappe.logger().info("[SMARTFLOW STATUS MAPPING] Returning: In Progress (has answered agent)")
		return "In Progress"

	frappe.logger().info("[SMARTFLOW STATUS MAPPING] Returning: Initiated (default)")
	return "Initiated"



def validate_webhook_token():
	"""
	Validate webhook token from Smartflo.
	
	Smartflo can send auth in multiple formats:
	1. Authorization: <api_key>:<api_secret>
	2. Authorization: Bearer <api_key>:<api_secret>
	3. Authorization: token <api_key>:<api_secret>
	4. X-Auth-Token: <api_key>:<api_secret>
	5. X-Webhook-Token: <api_key>:<api_secret>
	"""

	try:
		settings = TataTeleSettings.get_settings()
		
		if not settings:
			frappe.logger().error("[SMARTFLOW AUTH] Settings not found")
			return False
		
		expected = (settings.get_password("webhook_token") or "").strip()
		
		if not expected:
			frappe.logger().warning("[SMARTFLOW AUTH] No webhook token configured - allowing all requests")
			return True
		
		# Try multiple header names
		auth_header = (
			frappe.request.headers.get("Authorization") or
			frappe.request.headers.get("X-Auth-Token") or
			frappe.request.headers.get("X-Webhook-Token") or
			""
		).strip()
		
		if not auth_header:
			frappe.logger().error("[SMARTFLOW AUTH] No authorization header found")
			# Log all headers for debugging
			headers_dict = {k: v for k, v in frappe.request.headers.items()}
			frappe.logger().error(f"[SMARTFLOW AUTH] All headers: {headers_dict}")
			return False
		
		# Extract token from various formats
		received_token = auth_header
		
		# Remove "Bearer " prefix if present
		if received_token.lower().startswith("bearer "):
			received_token = received_token[7:].strip()
		
		# Remove "token " prefix if present
		if received_token.lower().startswith("token "):
			received_token = received_token[6:].strip()
		
		# Compare tokens
		if received_token == expected:
			frappe.logger().info("[SMARTFLOW AUTH] Token validated successfully")
			return True
		else:
			frappe.logger().error(
				f"[SMARTFLOW AUTH] Token mismatch - "
				f"Expected length: {len(expected)}, Received length: {len(received_token)}"
			)
			# TEMPORARY: Log full tokens for debugging (remove after fixing)
			frappe.logger().error(f"[SMARTFLOW AUTH DEBUG] Expected token: {expected}")
			frappe.logger().error(f"[SMARTFLOW AUTH DEBUG] Received token: {received_token}")
			
			# Also log partial for quick comparison
			if len(expected) > 8:
				frappe.logger().error(f"[SMARTFLOW AUTH] Expected starts with: {expected[:4]}...{expected[-4:]}")
			if len(received_token) > 8:
				frappe.logger().error(f"[SMARTFLOW AUTH] Received starts with: {received_token[:4]}...{received_token[-4:]}")
			return False

	except Exception as e:
		frappe.logger().error(f"[SMARTFLOW AUTH] Exception: {str(e)}")
		frappe.log_error(frappe.get_traceback(), "Smartflow Auth Error")
		return False


def _find_or_create_call_log(ref_id, agent_no=None, customer_no=None):
	"""
	tabCRM Call Log has UNIQUE column `id`.
We store outbound ref_id in `id` so all webhook events update same row.
	"""
	name = frappe.db.get_value("CRM Call Log", {"id": ref_id}, "name")
	if name:
		return frappe.get_doc("CRM Call Log", name)

	doc = frappe.new_doc("CRM Call Log")
	doc.telephony_medium = "Tata Tele"
	doc.medium = "Smartflow"
	doc.type = "Outgoing"
	doc.id = ref_id
	doc.status = "Initiated"
	doc.start_time = frappe.utils.now_datetime()
	
	# Set caller to current user ONLY if they exist in User doctype
	try:
		current_user = frappe.session.user
		if current_user and current_user != "Guest":
			# Verify user exists before setting
			if frappe.db.exists("User", current_user):
				doc.caller = current_user
			else:
				frappe.logger().warning(f"[SMARTFLOW] User {current_user} not found, skipping caller field")
	except Exception as e:
		frappe.logger().warning(f"[SMARTFLOW] Could not set caller: {str(e)}")

	# store numbers as last 10 digits
	agent_no = _only_last_10(agent_no)
	customer_no = _only_last_10(customer_no)

	if agent_no:
		# "from" is reserved: use db.set_value after insert OR setattr safely
		try:
			setattr(doc, "from", agent_no)
		except Exception:
			pass
	if customer_no:
		try:
			setattr(doc, "to", customer_no)
		except Exception:
			pass

	# optional linking by customer number
	try:
		if customer_no:
			contact = get_contact_by_phone_number(customer_no) or {}
			if contact.get("name"):
				doc.reference_doctype = "Contact"
				doc.reference_docname = contact.get("name")
				if contact.get("lead"):
					doc.reference_doctype = "CRM Lead"
					doc.reference_docname = contact.get("lead")
				elif contact.get("deal"):
					doc.reference_doctype = "CRM Deal"
					doc.reference_docname = contact.get("deal")
	except Exception as e:
		frappe.logger().warning(f"[SMARTFLOW] Could not link contact: {str(e)}")

	doc.insert(ignore_permissions=True)
	frappe.db.commit()

	# ensure "from" is saved (safe for reserved field)
	if agent_no:
		frappe.db.set_value("CRM Call Log", doc.name, "from", agent_no)
	if customer_no:
		frappe.db.set_value("CRM Call Log", doc.name, "to", customer_no)
	frappe.db.commit()

	return frappe.get_doc("CRM Call Log", doc.name)


def _publish_realtime(ref_id, doc, payload):
	"""Publish real-time updates to frontend via socket"""
	data = {
		"ref_id": ref_id,
		"status": doc.status,
		"duration": doc.duration,
		"recording_url": doc.recording_url,
		"call_status": payload.get("call_status"),
		"call_id": _extract_call_id(payload),
	}
	
	frappe.publish_realtime("tata_tele_call", data)
	
	# Also log for debugging
	frappe.logger().info(f"[TATA TELE REALTIME] Published: {data}")


# =========================================================
# Click to call (Outbound)
# =========================================================

@frappe.whitelist()
def make_a_call(to_number, from_number=None):
	"""
	1) Generate ref_id
	2) Insert CRM Call Log immediately with id=ref_id
	3) Hit click_to_call API with ref_id
	4) Return ref_id + agent_number/caller_id/data for frontend
	"""
	if not is_integration_enabled():
		frappe.throw(_("Please setup Tata Tele integration"), title=_("Integration Not Enabled"))

	settings = TataTeleSettings.get_settings()
	if not settings:
		frappe.throw(_("Tata Tele Settings not configured"), title=_("Configuration Missing"))

	# per-user mapping (optional)
	agent_number = settings.agent_number
	caller_id = settings.caller_id or settings.agent_number

	if frappe.db.exists("DocType", "Smartflo Agent Mapping"):
		mapping = frappe.db.get_value(
			"Smartflo Agent Mapping",
			{"user": frappe.session.user},
			["agent_number", "caller_id"],
			as_dict=True
		)
		if mapping:
			agent_number = mapping.agent_number or agent_number
			caller_id = mapping.caller_id or caller_id

	if not to_number:
		frappe.throw(_("Destination number is required"), title=_("Invalid Input"))

	api_endpoint = settings.api_endpoint
	api_token = settings.get_password("api_token")

	ref_id = str(uuid.uuid4())

	# create call log now (store last 10 digits)
	doc = _find_or_create_call_log(
		ref_id,
		agent_no=_only_last_10(agent_number),
		customer_no=_only_last_10(to_number)
	)

	payload = {
		"agent_number": agent_number,
		"destination_number": to_number,
		"caller_id": caller_id,
		"async": 1,
		"ref_id": ref_id,
	}

	headers = {"Authorization": f"Bearer {api_token}", "Content-Type": "application/json"}

	resp = requests.post(api_endpoint, json=payload, headers=headers, timeout=60)
	if resp.status_code not in (200, 201):
		frappe.db.set_value("CRM Call Log", doc.name, "status", "Failed")
		frappe.db.commit()
		frappe.throw(_("Tata Tele API Error: {0}").format(resp.text), title=_("API Error"))

	data = resp.json() if resp.text else {}
	call_id = data.get("call_id") or data.get("id") or data.get("request_id")

	# Save provider call_id in note (no dedicated column in your table)
	if call_id:
		frappe.db.set_value("CRM Call Log", doc.name, "note", f"smartflo_call_id={call_id}")
		frappe.db.commit()

	# Publish initial status to frontend
	frappe.publish_realtime("tata_tele_call", {
		"ref_id": ref_id,
		"status": "Initiated",
		"call_id": call_id,
		"duration": 0,
	})

	return {
		"ok": True,
		"success": True,
		"message": "Originate successfully queued",
		"ref_id": ref_id,
		"call_id": call_id or None,
		"agent_number": agent_number,
		"caller_id": caller_id,
		"data": data,
	}


# =========================================================
# Single webhook endpoint (3 outbound events)
# =========================================================

@frappe.whitelist(allow_guest=True, methods=["POST"])
def webhook_handler():
	frappe.local.no_csrf = True

	try:
		if not is_integration_enabled():
			frappe.logger().warning("[SMARTFLOW] Integration not enabled")
			frappe.local.response.http_status_code = 503
			return {"success": False, "message": "Integration not enabled"}

		# Validate authentication
		if not validate_webhook_token():
			frappe.logger().error("[SMARTFLOW] Webhook authentication FAILED - returning 401")
			frappe.local.response.http_status_code = 401
			return {"success": False, "error": "Unauthorized", "message": "Invalid or missing webhook token"}

		frappe.logger().info("[SMARTFLOW] Webhook authenticated successfully")

		payload = _get_json()

		# DEBUG: print full webhook payload
		frappe.logger().info("[SMARTFLOW OUTBOUND WEBHOOK] Payload:\n" + json.dumps(payload, indent=2))

		# DEBUG: quick key fields
		frappe.logger().info(
			"[SMARTFLOW] call_status="
			+ str(payload.get("call_status"))
			+ " direction=" + str(payload.get("direction"))
			+ " end_stamp=" + str(payload.get("end_stamp"))
			+ " answer_stamp=" + str(payload.get("answer_stamp"))
			+ " answer_agent_number=" + str(payload.get("answer_agent_number"))
			+ " billsec=" + str(payload.get("billsec"))
		)

		ref_id = _extract_ref_id(payload)
		
		# Enhanced logging for debugging
		frappe.logger().info(f"[SMARTFLOW] Extracted ref_id: {ref_id}")
		frappe.logger().info(f"[SMARTFLOW] Payload keys: {list(payload.keys())}")
		
		if not ref_id:
			# Log the full payload for debugging when ref_id is missing
			frappe.logger().warning(f"[SMARTFLOW] ref_id missing! This might be an inbound call or test webhook.")
			frappe.logger().warning(f"[SMARTFLOW] Payload: {json.dumps(payload, indent=2)}")
			
			# Check if this is an inbound call (has different structure)
			call_type = payload.get("call_type") or payload.get("type") or payload.get("direction") or "unknown"
			frappe.logger().info(f"[SMARTFLOW] Call type/direction: {call_type}")
			
			# Return 200 OK to acknowledge receipt, but don't process
			return {
				"success": True, 
				"message": "Webhook received but ref_id missing - might be inbound call or test",
				"call_type": call_type,
				"payload_keys": list(payload.keys())
			}

		agent_no = _extract_agent(payload)
		customer_no = _extract_customer(payload)

		# find/create by id=ref_id
		doc = _find_or_create_call_log(ref_id, agent_no=agent_no, customer_no=customer_no)

		frappe.logger().info(f"[SMARTFLOW] Found/Created Call Log: {doc.name}, Current Status: {doc.status}")

		new_status = _map_status(payload)
		
		frappe.logger().info(f"[SMARTFLOW] Mapped Status: {new_status}")

		start_time = _extract_start(payload) or doc.start_time or frappe.utils.now_datetime()
		end_time = _extract_end(payload)
		duration = _extract_duration(payload)
		recording_url = _extract_recording(payload)
		call_id = _extract_call_id(payload)
		
		# Extract additional fields
		answered_agent = _extract_answered_agent(payload)
		missed_agent = _extract_missed_agent(payload)
		hangup_cause = _extract_hangup_cause(payload)
		call_connected = _extract_call_connected(payload)
		
		frappe.logger().info(
			f"[SMARTFLOW] Extracted - Duration: {duration}, End Time: {end_time}, "
			f"Recording: {recording_url}, Answered Agent: {answered_agent}, "
			f"Missed Agent: {missed_agent}, Hangup Cause: {hangup_cause}, "
			f"Call Connected: {call_connected}"
		)

		updates = {"status": new_status}

		# numbers (always last 10 digits)
		if agent_no:
			updates["from"] = _only_last_10(agent_no)
		if customer_no:
			updates["to"] = _only_last_10(customer_no)

		# start time only if empty
		if not doc.start_time:
			updates["start_time"] = start_time

		# final state => end time
		if new_status in ("Completed", "No answer", "Failed", "Busy", "Cancelled"):
			updates["end_time"] = end_time or frappe.utils.now_datetime()

		# duration: save on final states
		if duration is not None and new_status in ("Completed", "No answer"):
			updates["duration"] = duration

		# recording: only on completed
		if recording_url and new_status == "Completed":
			updates["recording_url"] = recording_url

		# save call_id and hangup_cause into note (max 140 chars for Text field)
		note_parts = []
		if call_id:
			note_parts.append(f"call_id={call_id}")
		if hangup_cause:
			# Truncate hangup cause if too long
			cause_str = str(hangup_cause)[:50]
			note_parts.append(f"hangup={cause_str}")
		if answered_agent:
			# Truncate agent name if too long
			agent_str = str(answered_agent)[:30]
			note_parts.append(f"agent={agent_str}")
		if missed_agent:
			missed_str = str(missed_agent)[:30]
			note_parts.append(f"missed={missed_str}")
		
		if note_parts:
			# Join and ensure total length is under 140 chars
			note_text = ", ".join(note_parts)
			updates["note"] = note_text[:140]

		# apply updates safely (because "from" is reserved)
		for k, v in updates.items():
			if k == "from":
				frappe.db.set_value("CRM Call Log", doc.name, "from", v)
			else:
				frappe.db.set_value("CRM Call Log", doc.name, k, v)

		frappe.db.commit()
		doc.reload()
		
		frappe.logger().info(f"[SMARTFLOW] Updates Applied - Final Status: {doc.status}, Duration: {doc.duration}, End Time: {doc.end_time}")

		_publish_realtime(ref_id, doc, payload)

		return {
			"success": True,
			"ref_id": ref_id,
			"status": doc.status,
			"duration": doc.duration,
			"recording_url": doc.recording_url,
		}
	
	except Exception as e:
		frappe.logger().error(f"[SMARTFLOW] Exception in webhook_handler: {str(e)}")
		frappe.log_error(frappe.get_traceback(), "Smartflow Webhook Error")
		frappe.local.response.http_status_code = 500
		return {
			"success": False,
			"error": "Internal server error",
			"message": str(e)
		}


# @frappe.whitelist(allow_guest=True, methods=["POST"])
# def webhook_handler():
# 	frappe.local.no_csrf = True

# 	print("\n================ SMARTFLOW WEBHOOK RECEIVED ================\n")

# 	if not is_integration_enabled():
# 		print("❌ Integration not enabled")
# 		return {"success": False, "message": "Integration not enabled"}

# 	auth_header = frappe.request.headers.get("Authorization")
# 	print("🔐 Authorization Header:", auth_header)

# 	if not validate_webhook_token():
# 		print("❌ Webhook token validation FAILED")
# 		frappe.local.response.http_status_code = 401
# 		return {"success": False, "error": "Unauthorized"}

# 	print("✅ Webhook token validated successfully")

# 	payload = _get_json()

# 	print("\n📦 FULL PAYLOAD RECEIVED:")
# 	print(json.dumps(payload, indent=2))
# 	print("\n------------------------------------------------------------")

# 	ref_id = _extract_ref_id(payload)
# 	print("🔎 Extracted ref_id:", ref_id)

# 	if not ref_id:
# 		print("❌ ref_id missing in webhook")
# 		frappe.local.response.http_status_code = 400
# 		return {"success": False, "error": "ref_id missing"}

# 	agent_no = _extract_agent(payload)
# 	customer_no = _extract_customer(payload)

# 	print("📞 Agent Number (cleaned):", agent_no)
# 	print("📱 Customer Number (cleaned):", customer_no)

# 	doc = _find_or_create_call_log(ref_id, agent_no=agent_no, customer_no=customer_no)

# 	print("📄 Found/Created Call Log:", doc.name)

# 	new_status = _map_status(payload)
# 	print("📌 Mapped Status:", new_status)

# 	start_time = _extract_start(payload)
# 	answer_time = _extract_answer(payload)
# 	end_time = _extract_end(payload)
# 	duration = _extract_duration(payload)
# 	recording_url = _extract_recording(payload)
# 	call_id = _extract_call_id(payload)

# 	print("⏱ Start Time:", start_time)
# 	print("⏱ Answer Time:", answer_time)
# 	print("⏱ End Time:", end_time)
# 	print("⏱ Duration:", duration)
# 	print("🎧 Recording URL:", recording_url)
# 	print("🆔 Provider Call ID:", call_id)

# 	print("\n---------------- APPLYING UPDATES ----------------")

# 	updates = {"status": new_status}

# 	if agent_no:
# 		updates["from"] = agent_no

# 	if customer_no:
# 		updates["to"] = customer_no

# 	if new_status in ("Completed", "No answer", "Failed", "Busy", "Cancelled"):
# 		updates["end_time"] = end_time or frappe.utils.now_datetime()

# 	if duration is not None and new_status in ("Completed", "No answer"):
# 		updates["duration"] = duration

# 	if recording_url and new_status == "Completed":
# 		updates["recording_url"] = recording_url

# 	if call_id:
# 		updates["note"] = f"smartflo_call_id={call_id}"

# 	print("📥 Final Updates Dict:")
# 	print(json.dumps(updates, indent=2))

# 	# Apply updates
# 	for k, v in updates.items():
# 		if k == "from":
# 			frappe.db.set_value("CRM Call Log", doc.name, "from", v)
# 		else:
# 			frappe.db.set_value("CRM Call Log", doc.name, k, v)

# 	frappe.db.commit()
# 	doc.reload()

# 	print("\n✅ FINAL STATUS IN DB:", doc.status)
# 	print("✅ FINAL DURATION IN DB:", doc.duration)
# 	print("============================================================\n")

# 	_publish_realtime(ref_id, doc, payload)

# 	return {
# 		"success": True,
# 		"ref_id": ref_id,
# 		"status": doc.status,
# 		"duration": doc.duration,
# 		"recording_url": doc.recording_url,
# 	}


# =========================================================
# Hangup Call (Outbound Cancel)
# =========================================================

@frappe.whitelist()
def hangup_call(call_id: str, ref_id: str = None):
	"""
	Hangup an ongoing Smartflo call.

	Args:
		call_id (str): Smartflo provider call_id (mandatory)
		ref_id (str): Our CRM ref_id (optional, used to update call log)

	Returns:
		JSON response for frontend
	"""

	if not is_integration_enabled():
		frappe.throw(_("Integration not enabled"), title=_("Not Enabled"))

	if not call_id:
		frappe.throw(_("call_id is required"), title=_("Invalid Input"))

	settings = TataTeleSettings.get_settings()
	if not settings:
		frappe.throw(_("Tata Tele Settings not configured"))

	api_token = settings.get_password("api_token")

	url = "https://api-smartflo.tatateleservices.com/v1/call/hangup"

	headers = {
		"Authorization": f"Bearer {api_token}",
		"Content-Type": "application/json",
		"Accept": "application/json",
	}

	payload = {
		"call_id": call_id
	}

	try:
		resp = requests.post(url, json=payload, headers=headers, timeout=30)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Smartflo Hangup API Error")
		frappe.throw(_("Failed to connect to Tata Tele API"))

	if resp.status_code not in (200, 201):
		frappe.throw(_("Hangup failed: {0}").format(resp.text))

	data = resp.json() if resp.text else {}

	# 🔄 Update CRM Call Log if ref_id provided
	if ref_id:
		name = frappe.db.get_value("CRM Call Log", {"id": ref_id}, "name")
		if name:
			frappe.db.set_value("CRM Call Log", name, {
				"status": "Cancelled",
				"end_time": frappe.utils.now_datetime()
			})
			frappe.db.commit()
			
			# Publish real-time update
			frappe.publish_realtime("tata_tele_call", {
				"ref_id": ref_id,
				"status": "Cancelled",
				"call_id": call_id,
			})

	return {
		"success": True,
		"message": "Call hangup request sent successfully",
		"call_id": call_id,
		"provider_response": data
	}

