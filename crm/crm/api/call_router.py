import frappe
import json
from crm.integrations.api import get_contact_by_phone_number

# =========================================================
# Utilities
# =========================================================

def _get_json():
    try:
        return frappe.request.get_json() or {}
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
        val = d.get(k)
        if val not in (None, ""):
            return val
    return None

def _norm_num(v):
    if not v:
        return None
    s = str(v).strip()
    out = []
    for ch in s:
        if ch.isdigit() or ch == "+":
            out.append(ch)
    return "".join(out) or None

def _parse_dt(v):
    # Smartflow: "2025-01-17 16:36:14"
    if not v:
        return None
    try:
        return frappe.utils.get_datetime(str(v).strip())
    except Exception:
        return None

def _call_key(payload):
    # id field in CRM Call Log is UNIQUE; use call_id first
    call_id = _pick(payload, ["call_id", "callId", "callid"])
    uuid = _pick(payload, ["uuid", "UUID"])
    key = call_id or uuid or ("TATA-" + frappe.generate_hash(length=12))
    return str(key)[:140]

# ---------- YOUR SMARTFLOW KEYS (exact) ----------

def _extract_customer(payload):
    # customer number (who called)
    # note: you had "customer_no_with_prefix " with trailing space in templates
    return _norm_num(_pick(payload, [
        "customer_no_with_prefix",
        "customer_no_with_prefix ",
        "customer_number_with_prefix",
        "customer_number_with_prefix ",
        "customer_no",
        "customer_number",
        "from",
        "caller",
        "caller_number",
        "from_number"
    ]))

def _extract_did(payload):
    # DID/virtual number dialed by customer
    return _norm_num(_pick(payload, [
        "call_to_number",     # ✅ main
        "did_number",
        "virtual_number",
        "to"
    ]))

def _extract_answered_agent_number(payload):
    # answered agent number differs between answered vs completed payload
    return _norm_num(_pick(payload, [
        "answer_agent_number",        # ✅ answered payload
        "answered_agent_number",      # ✅ hangup/completed payload
        "answered_agent",
        "agent_number"
    ]))

def _extract_duration_seconds(payload):
    # prefer billsec for billing/talk time
    d = _pick(payload, ["billsec", "duration", "call_duration", "duration_seconds"])
    if d in (None, ""):
        return None
    try:
        return int(float(str(d).strip()))
    except Exception:
        return None

def _extract_recording_url(payload):
    rec = _pick(payload, ["recording_url", "recordingUrl"])
    if not rec:
        return None
    return str(rec).strip()[:140]  # DB is varchar(140)

def _extract_start_dt(payload):
    return _parse_dt(_pick(payload, ["start_stamp", "start_time", "start"]))

def _extract_end_dt(payload):
    return _parse_dt(_pick(payload, ["end_stamp", "end_time", "end"]))

# =========================================================
# Security / Token check (optional)
# =========================================================

# def validate_webhook():
#     try:
#         settings = frappe.get_single("CRM Tata Tele Settings")
#         if not getattr(settings, "enabled", 0):
#             return True
#         token = getattr(settings, "webhook_token", None)
#         if not token:
#             return True

#         headers = frappe.local.request.headers
#         got = (
#             headers.get("X-Webhook-Token")
#             or headers.get("X-Tata-Tele-Token")
#             or headers.get("Authorization")
#         )
#         if not got:
#             return False
#         if got.startswith("Bearer "):
#             got = got[7:]
#         return got.strip() == token.strip()
#     except Exception:
#         # fail-open (as you were doing). change to False if you want strict security.
#         return True

def validate_webhook():
	"""
	Smartflo header MUST be:
	Authorization: token <api_key>:<api_secret>

	Frappe Setting (Webhook Token):
	<api_key>:<api_secret>
	"""

	try:
		settings = frappe.get_single("CRM Tata Tele Settings")

		# If integration disabled, allow
		if not getattr(settings, "enabled", 0):
			return True

		expected = (settings.get_password("webhook_token") or "").strip()

		# If empty => allow (optional security off)
		if not expected:
			return True

		auth_header = (frappe.local.request.headers.get("Authorization") or "").strip()

		if not auth_header:
			return False

		if not auth_header.lower().startswith("token "):
			return False

		got = auth_header[6:].strip()

		# Debug log
		frappe.logger().info(
			f"[SMARTFLOW INBOUND AUTH] expected='{expected}' got='{got}' raw='{auth_header}'"
		)

		return got == expected

	except Exception:
		frappe.log_error(frappe.get_traceback(), "Inbound webhook token validation failed")
		return False

# =========================================================
# Agent mapping: answered agent number -> CRM User
# =========================================================

def _map_agent_number_to_user(agent_number):
    """
    Map Smartflow answered agent number → CRM User using Smartflo Agent Mapping doctype.
    Expected fields: user, agent_number
    """
    if not agent_number:
        return None
    try:
        # try exact
        mapping = frappe.db.exists("Smartflo Agent Mapping", {"agent_number": agent_number})
        # try last 10 digits
        if not mapping and len(agent_number) >= 10:
            mapping = frappe.db.exists("Smartflo Agent Mapping", {"agent_number": agent_number[-10:]})
        if mapping:
            doc = frappe.get_doc("Smartflo Agent Mapping", mapping)
            return doc.user
    except Exception:
        frappe.log_error(frappe.get_traceback(), "Smartflo mapping lookup failed")
    return None

# =========================================================
# Upsert CRM Call Log
# =========================================================

# def upsert_call_log(event, payload):
#     """
#     event: received | answered | completed
#     """
#     call_key = _call_key(payload)

#     customer = _extract_customer(payload)                 # customer_no_with_prefix
#     did = _extract_did(payload)                           # call_to_number
#     answered_agent_no = _extract_answered_agent_number(payload)

#     receiver_user = _map_agent_number_to_user(answered_agent_no) if answered_agent_no else None

#     duration = _extract_duration_seconds(payload)         # billsec preferred
#     rec_url = _extract_recording_url(payload)

#     start_dt = _extract_start_dt(payload) or frappe.utils.now_datetime()
#     end_dt = _extract_end_dt(payload)

#     existing_name = frappe.db.exists("CRM Call Log", {"id": call_key})

#     # -------------------------
#     # CREATE
#     # -------------------------
#     if not existing_name:
#         try:
#             doc = frappe.new_doc("CRM Call Log")
#             doc.set("id", call_key)
#             doc.set("type", "Incoming")
#             doc.set("telephony_medium", "Tata Tele")
#             doc.set("medium", "Smartflow")

#             if customer:
#                 doc.set("from", customer)
#             if did:
#                 doc.set("to", did)

#             # times
#             doc.set("start_time", start_dt)

#             # default duration (DECIMAL) as number
#             doc.set("duration", 0)

#             if event == "received":
#                 doc.set("status", "Ringing")

#             elif event == "answered":
#                 doc.set("status", "In Progress")
#                 if receiver_user:
#                     doc.set("receiver", receiver_user)

#             elif event == "completed":
#                 doc.set("status", "Completed")
#                 if receiver_user:
#                     doc.set("receiver", receiver_user)
#                 if duration is not None:
#                     doc.set("duration", duration)
#                 doc.set("end_time", end_dt or frappe.utils.now_datetime())
#                 if rec_url:
#                     doc.set("recording_url", rec_url)

#             else:
#                 doc.set("status", "Initiated")

#             # IMPORTANT: do NOT set "note" unless you're sure it's a Data field in DocType UI.
#             # Your DB shows varchar(140), but earlier you got "Could not find Note" errors.
#             # So we skip note completely to avoid validation failures.

#             doc.insert(ignore_permissions=True)
#             frappe.db.commit()
#             return doc.name, call_key

#         except Exception:
#             frappe.log_error(frappe.get_traceback(), "CRM Call Log insert failed")
#             return None, call_key

#     # -------------------------
#     # UPDATE
#     # -------------------------
#     try:
#         updates = {}

#         if customer:
#             updates["from"] = customer
#         if did:
#             updates["to"] = did

#         # keep start_time stable: only set if empty in db
#         if frappe.db.get_value("CRM Call Log", existing_name, "start_time") in (None, ""):
#             updates["start_time"] = start_dt

#         if event == "received":
#             updates["status"] = "Ringing"

#         elif event == "answered":
#             updates["status"] = "In Progress"
#             if receiver_user:
#                 updates["receiver"] = receiver_user

#         elif event == "completed":
#             updates["status"] = "Completed"
#             if receiver_user:
#                 updates["receiver"] = receiver_user
#             if duration is not None:
#                 updates["duration"] = duration
#             updates["end_time"] = end_dt or frappe.utils.now_datetime()
#             if rec_url:
#                 updates["recording_url"] = rec_url

#         # apply updates
#         for k, v in updates.items():
#             if k == "from":
#                 frappe.db.set_value("CRM Call Log", existing_name, "from", v)
#             else:
#                 frappe.db.set_value("CRM Call Log", existing_name, k, v)

#         frappe.db.commit()
#         return existing_name, call_key

#     except Exception:
#         frappe.log_error(frappe.get_traceback(), "CRM Call Log update failed")
#         return None, call_key

def upsert_call_log(event, payload):
    """
    event: received | answered | completed
    """
    call_key = _call_key(payload)

    customer = _extract_customer(payload)                 # customer_no_with_prefix
    did = _extract_did(payload)                           # call_to_number
    answered_agent_no = _extract_answered_agent_number(payload)

    receiver_user = _map_agent_number_to_user(answered_agent_no) if answered_agent_no else None

    duration = _extract_duration_seconds(payload)         # billsec preferred
    rec_url = _extract_recording_url(payload)

    start_dt = _extract_start_dt(payload) or frappe.utils.now_datetime()
    end_dt = _extract_end_dt(payload)

    # ✅ Find CRM entity by phone number (Lead/Deal/Contact)
    # Expecting your method to return something like:
    # {"name": "...", "lead": "...", "deal": "..."}
    contact_info = {}
    try:
        if customer:
            frappe.logger().info(f"[SMARTFLOW INBOUND] Looking up contact by phone: {customer}")
            contact_info = get_contact_by_phone_number(customer) or {}
            frappe.logger().info(f"[SMARTFLOW INBOUND] Contact lookup result: {contact_info}")
    except Exception:
        frappe.log_error(frappe.get_traceback(), "get_contact_by_phone_number failed")

    # ✅ Decide reference (Lead > Deal > Contact)
    ref_doctype = None
    ref_docname = None
    if contact_info.get("lead"):
        ref_doctype = "CRM Lead"
        ref_docname = contact_info.get("lead")
        frappe.logger().info(f"[SMARTFLOW INBOUND] Linking to Lead: {ref_docname}")
    elif contact_info.get("deal"):
        ref_doctype = "CRM Deal"
        ref_docname = contact_info.get("deal")
        frappe.logger().info(f"[SMARTFLOW INBOUND] Linking to Deal: {ref_docname}")
    elif contact_info.get("name"):
        ref_doctype = "Contact"
        ref_docname = contact_info.get("name")
        frappe.logger().info(f"[SMARTFLOW INBOUND] Linking to Contact: {ref_docname}")
    else:
        frappe.logger().warning(f"[SMARTFLOW INBOUND] No Lead/Deal/Contact found for phone: {customer}")

    existing_name = frappe.db.exists("CRM Call Log", {"id": call_key})

    # -------------------------
    # CREATE
    # -------------------------
    if not existing_name:
        try:
            doc = frappe.new_doc("CRM Call Log")
            doc.set("id", call_key)
            doc.set("type", "Incoming")
            doc.set("telephony_medium", "Tata Tele")
            doc.set("medium", "Smartflow")

            # ✅ save numbers
            if customer:
                doc.set("from", customer)
                # Don't set "caller" - it's a Link field, not for phone numbers
            if did:
                doc.set("to", did)

            # ✅ link to Lead/Deal/Contact (this makes it appear in Activities)
            if ref_doctype and ref_docname:
                doc.set("reference_doctype", ref_doctype)
                doc.set("reference_docname", ref_docname)

            # ✅ receiver mapping
            if receiver_user:
                doc.set("receiver", receiver_user)

            # times
            doc.set("start_time", start_dt)

            # default duration
            doc.set("duration", 0)

            # status updates
            if event == "received":
                doc.set("status", "Ringing")

            elif event == "answered":
                doc.set("status", "In Progress")

            elif event == "completed":
                doc.set("status", "Completed")
                if duration is not None:
                    doc.set("duration", duration)
                doc.set("end_time", end_dt or frappe.utils.now_datetime())
                if rec_url:
                    doc.set("recording_url", rec_url)

            else:
                doc.set("status", "Initiated")

            doc.insert(ignore_permissions=True)
            frappe.db.commit()
            return doc.name, call_key

        except Exception:
            frappe.log_error(frappe.get_traceback(), "CRM Call Log insert failed")
            return None, call_key

    # -------------------------
    # UPDATE
    # -------------------------
    try:
        updates = {}

        # ✅ save numbers
        if customer:
            updates["from"] = customer
            # Don't set "caller" - it's a Link field, not for phone numbers
        if did:
            updates["to"] = did

        # ✅ keep start_time stable
        if frappe.db.get_value("CRM Call Log", existing_name, "start_time") in (None, ""):
            updates["start_time"] = start_dt

        # ✅ always ensure reference is filled (activities)
        if ref_doctype and ref_docname:
            updates["reference_doctype"] = ref_doctype
            updates["reference_docname"] = ref_docname

        # ✅ receiver
        if receiver_user:
            updates["receiver"] = receiver_user

        if event == "received":
            updates["status"] = "Ringing"

        elif event == "answered":
            updates["status"] = "In Progress"

        elif event == "completed":
            updates["status"] = "Completed"
            if duration is not None:
                updates["duration"] = duration
            updates["end_time"] = end_dt or frappe.utils.now_datetime()
            if rec_url:
                updates["recording_url"] = rec_url

        # apply updates safely (because "from" is reserved)
        for k, v in updates.items():
            if k == "from":
                frappe.db.set_value("CRM Call Log", existing_name, "from", v)
            else:
                frappe.db.set_value("CRM Call Log", existing_name, k, v)

        frappe.db.commit()
        return existing_name, call_key

    except Exception:
        frappe.log_error(frappe.get_traceback(), "CRM Call Log update failed")
        return None, call_key


# =========================================================
# Webhook Endpoints
# =========================================================

@frappe.whitelist(allow_guest=True, methods=["POST"])
def smartflow_inbound_received():
    frappe.local.no_csrf = True
    
    try:
        frappe.logger().info("[SMARTFLOW INBOUND] Received webhook called")
        
        if not validate_webhook():
            frappe.logger().warning("[SMARTFLOW INBOUND] Webhook validation failed")
            frappe.local.response.http_status_code = 401
            return {"success": False, "error": "Unauthorized"}

        payload = _get_json()
        frappe.logger().info(f"[SMARTFLOW INBOUND] Payload: {json.dumps(payload, indent=2)}")
        
        name, call_id = upsert_call_log("received", payload)
        
        frappe.logger().info(f"[SMARTFLOW INBOUND] Call log created/updated: {name}, call_id: {call_id}")

        if not name:
            frappe.local.response.http_status_code = 500
            return {"success": False, "event": "received", "error": "Insert failed. Check Error Log.", "call_id": call_id}

        return {"success": True, "event": "received", "call_log": name, "call_id": call_id}
        
    except Exception as e:
        frappe.logger().error(f"[SMARTFLOW INBOUND] Exception in smartflow_inbound_received: {str(e)}")
        frappe.log_error(frappe.get_traceback(), "Smartflow Inbound Received Error")
        frappe.local.response.http_status_code = 500
        return {"success": False, "error": str(e)}

@frappe.whitelist(allow_guest=True, methods=["POST"])
def smartflow_inbound_answered():
    frappe.local.no_csrf = True
    
    try:
        frappe.logger().info("[SMARTFLOW INBOUND] Answered webhook called")
        
        if not validate_webhook():
            frappe.logger().warning("[SMARTFLOW INBOUND] Webhook validation failed")
            frappe.local.response.http_status_code = 401
            return {"success": False, "error": "Unauthorized"}

        payload = _get_json()
        frappe.logger().info(f"[SMARTFLOW INBOUND] Payload: {json.dumps(payload, indent=2)}")
        
        name, call_id = upsert_call_log("answered", payload)
        
        frappe.logger().info(f"[SMARTFLOW INBOUND] Call log updated: {name}, call_id: {call_id}")

        if not name:
            frappe.local.response.http_status_code = 500
            return {"success": False, "event": "answered", "error": "Update failed. Check Error Log.", "call_id": call_id}

        return {"success": True, "event": "answered", "call_log": name, "call_id": call_id}
        
    except Exception as e:
        frappe.logger().error(f"[SMARTFLOW INBOUND] Exception in smartflow_inbound_answered: {str(e)}")
        frappe.log_error(frappe.get_traceback(), "Smartflow Inbound Answered Error")
        frappe.local.response.http_status_code = 500
        return {"success": False, "error": str(e)}

@frappe.whitelist(allow_guest=True, methods=["POST"])
def smartflow_inbound_completed():
    frappe.local.no_csrf = True
    
    try:
        frappe.logger().info("[SMARTFLOW INBOUND] Completed webhook called")
        
        if not validate_webhook():
            frappe.logger().warning("[SMARTFLOW INBOUND] Webhook validation failed")
            frappe.local.response.http_status_code = 401
            return {"success": False, "error": "Unauthorized"}

        payload = _get_json()
        frappe.logger().info(f"[SMARTFLOW INBOUND] Payload: {json.dumps(payload, indent=2)}")
        
        name, call_id = upsert_call_log("completed", payload)
        
        frappe.logger().info(f"[SMARTFLOW INBOUND] Call log completed: {name}, call_id: {call_id}")

        if not name:
            frappe.local.response.http_status_code = 500
            return {"success": False, "event": "completed", "error": "Update failed. Check Error Log.", "call_id": call_id}

        return {"success": True, "event": "completed", "call_log": name, "call_id": call_id}
        
    except Exception as e:
        frappe.logger().error(f"[SMARTFLOW INBOUND] Exception in smartflow_inbound_completed: {str(e)}")
        frappe.log_error(frappe.get_traceback(), "Smartflow Inbound Completed Error")
        frappe.local.response.http_status_code = 500
        return {"success": False, "error": str(e)}
