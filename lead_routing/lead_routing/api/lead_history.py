# Copyright (c) 2026, IP CRM and contributors
# For license information, please see license.txt

"""
Lead history API — role-based views:
  • Non-admin users see leads they previously acted on (exited department log entries).
  • Admin / System Manager users see all completed/rejected leads globally,
    or a specific user's history when the `user` filter is set.
"""

import frappe
from frappe.utils import get_fullname


def _is_admin():
    """Check if the current session user is Administrator or System Manager."""
    roles = frappe.get_roles(frappe.session.user)
    return "Administrator" in roles or "System Manager" in roles


def _get_personal_history(user):
    """
    Return leads that `user` previously worked on — i.e. Lead Department Log
    entries where assigned_user == user AND exited_at is set (work is done).
    Each lead includes its current_department so the user can see where
    the lead is now after they handled it.
    """
    # Combine entries where user was assigned OR was the one who modified/exited the stage
    # (Using separate queries as complex OR filters can be inconsistent in some Frappe versions)
    fields = ["parent", "department", "entered_at", "exited_at", "action"]
    
    # 1. Logs explicitly assigned to the user (includes active ones for native completion check)
    assigned_entries = frappe.get_all("Lead Department Log", 
        filters={"parenttype": "CRM Lead", "assigned_user": user},
        fields=fields, order_by="entered_at desc", limit_page_length=2000
    )
    
    # 2. Logs the user acted on/exited (even if not assigned, e.g. Admin transfers)
    # We only want CLOSED logs here to avoid current stage hiding history during deduplication
    modified_entries = frappe.get_all("Lead Department Log", 
        filters={
            "parenttype": "CRM Lead", 
            "modified_by": user,
            "exited_at": ["!=", None]
        },
        fields=fields, order_by="entered_at desc", limit_page_length=2000
    )
    
    # Combine and sort to handle duplication and ordering properly
    history_entries = assigned_entries + modified_entries
    history_entries.sort(key=lambda x: str(x.entered_at), reverse=True)
    
    if not history_entries:
        return {
            "leads": [],
            "user": user,
            "full_name": get_fullname(user),
            "view_type": "personal",
        }

    # Deduplicate leads — keep the most recent log action per lead
    seen = {}
    active_user_leads = []
    
    for h in history_entries:
        if h.parent not in seen:
            seen[h.parent] = h
            if h.exited_at:
                pass # Already completed this phase
            else:
                active_user_leads.append(h.parent)

    lead_names = [name for name, entry in seen.items() if entry.exited_at]

    if active_user_leads:
        done_leads = frappe.get_all(
            "CRM Lead",
            filters={"name": ("in", active_user_leads)},
            fields=["name", "status", "department_status"],
            limit_page_length=2000,
        )
        for dl in done_leads:
            if dl.status == "Completed" or dl.department_status in ("Done", "Rejected"):
                lead_names.append(dl.name)

    if not lead_names:
        return {
            "leads": [],
            "user": user,
            "full_name": get_fullname(user),
            "view_type": "personal",
        }

    leads_data = frappe.get_all(
        "CRM Lead",
        filters={"name": ("in", lead_names)},
        fields=[
            "name", "lead_name", "email", "mobile_no", "status",
            "current_department", "department_status",
            "modified",
        ],
        order_by="modified desc",
        limit_page_length=2000,
        ignore_permissions=True,
    )

    # Enrich each lead with the action the user performed
    for lead in leads_data:
        entry = seen.get(lead.name)
        if entry:
            lead["user_action"] = entry.action
            lead["action_department"] = entry.department
            lead["action_at"] = str(entry.exited_at) if entry.exited_at else None

    return {
        "leads": leads_data,
        "user": user,
        "full_name": get_fullname(user),
        "view_type": "personal",
    }


def _get_global_history():
    """
    Admin global view — all leads with department_status in Done / Rejected.
    Each lead is enriched with who last handled it.
    """
    leads_data = frappe.get_all(
        "CRM Lead",
        filters=[
            ["name", "is", "set"]  # Required dummy filter when using or_filters
        ],
        or_filters=[
            ["department_status", "in", ["Done", "Rejected"]],
            ["status", "=", "Completed"]
        ],
        fields=[
            "name", "lead_name", "email", "mobile_no",
            "current_department", "department_status", "status",
            "modified",
        ],
        order_by="modified desc",
        limit_page_length=2000,
        ignore_permissions=True,
    )

    if not leads_data:
        return {
            "leads": [],
            "view_type": "global",
            "done_count": 0,
            "rejected_count": 0,
        }

    lead_names = [l.name for l in leads_data]

    # Fetch the last department log entry per lead (the one with the latest exited_at)
    all_logs = frappe.get_all(
        "Lead Department Log",
        filters={
            "parent": ("in", lead_names),
            "parenttype": "CRM Lead",
        },
        fields=["parent", "assigned_user", "action", "department", "exited_at"],
        order_by="exited_at desc",
        limit_page_length=5000, # Large limit to cover all logs for the fetched leads
    )

    # Build map of lead → last log with an assigned user
    last_log_by_lead = {}
    for log in all_logs:
        if log.parent not in last_log_by_lead and log.assigned_user:
            last_log_by_lead[log.parent] = log

    for lead in leads_data:
        log = last_log_by_lead.get(lead.name)
        if log:
            lead["last_handled_by"] = log.assigned_user
            lead["last_handled_by_name"] = get_fullname(log.assigned_user)
            lead["last_action"] = log.action
        else:
            lead["last_handled_by"] = None
            lead["last_handled_by_name"] = "—"
            lead["last_action"] = None

    # Compute counts for stat cards
    done_count = sum(1 for l in leads_data if l.department_status == "Done" or l.status == "Completed")
    rejected_count = sum(1 for l in leads_data if l.department_status == "Rejected")

    return {
        "leads": leads_data,
        "done_count": done_count,
        "rejected_count": rejected_count,
        "view_type": "global",
    }


@frappe.whitelist()
def get_my_lead_history(user=None):
    """
    Main entry point — returns role-appropriate lead history.
    """
    current_user = frappe.session.user
    is_admin = _is_admin()

    # Non-admin requesting another user's history → deny
    if user and user != current_user and not is_admin:
        frappe.throw("You do not have permission to view other users' lead history.")

    # Admin with a user filter → personal history for that user
    if is_admin and user:
        return _get_personal_history(user)

    # Admin without user filter → global completed/rejected view
    if is_admin and not user:
        return _get_global_history()

    # Non-admin → personal history only
    return _get_personal_history(current_user)


@frappe.whitelist()
def get_lead_department_history(lead_name):
    """
    Returns the full department transition history for a specific lead.
    """
    frappe.has_permission("CRM Lead", doc=lead_name, ptype="read", throw=True)

    history = frappe.get_all(
        "Lead Department Log",
        filters={
            "parent": lead_name,
            "parenttype": "CRM Lead",
        },
        fields=[
            "department", "shift", "entered_at", "exited_at",
            "action", "assigned_user",
        ],
        order_by="entered_at asc",
    )

    # Add full names
    for entry in history:
        if entry.assigned_user:
            entry["assigned_user_name"] = get_fullname(entry.assigned_user)

    return history
