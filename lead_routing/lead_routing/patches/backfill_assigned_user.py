# Copyright (c) 2026, IP CRM and contributors
# For license information, please see license.txt

"""
One-time backfill: populate NULL assigned_user values in Lead Department Log.

Run via:
    bench --site <site> execute lead_routing.patches.backfill_assigned_user.execute
"""

import frappe


def execute():
    """
    For each Lead Department Log entry with NULL assigned_user,
    try to determine who was assigned using:
    1. The ToDo history for that lead around the same timeframe
    2. The lead_owner field on the CRM Lead
    """
    null_entries = frappe.db.sql("""
        SELECT ldl.name, ldl.parent, ldl.department, ldl.entered_at, ldl.exited_at
        FROM `tabLead Department Log` ldl
        WHERE ldl.assigned_user IS NULL OR ldl.assigned_user = ''
        ORDER BY ldl.creation ASC
    """, as_dict=True)

    if not null_entries:
        print("No NULL assigned_user entries found. Nothing to backfill.")
        return

    print(f"Found {len(null_entries)} entries with NULL assigned_user. Backfilling...")

    fixed = 0
    skipped = 0

    for entry in null_entries:
        user = _find_assigned_user(entry)
        if user:
            frappe.db.set_value(
                "Lead Department Log", entry.name,
                "assigned_user", user,
                update_modified=False,
            )
            fixed += 1
        else:
            skipped += 1

    frappe.db.commit()
    print(f"Backfill complete: {fixed} fixed, {skipped} could not be resolved.")


def _find_assigned_user(entry):
    """Try to determine assignment from ToDo or lead_owner."""

    # Strategy 1: Find a ToDo that was allocated for this lead
    # around the time window of this log entry
    filters = {
        "reference_type": "CRM Lead",
        "reference_name": entry.parent,
    }

    # Look for ToDos that overlap the log entry's time window
    todos = frappe.get_all(
        "ToDo",
        filters=filters,
        fields=["allocated_to", "date", "status", "creation"],
        order_by="creation asc",
    )

    if todos:
        # If the entry has an entered_at and exited_at, find the ToDo
        # whose creation falls within that window
        if entry.entered_at and entry.exited_at:
            for todo in todos:
                if entry.entered_at <= todo.creation <= entry.exited_at:
                    return todo.allocated_to

        # If no exact match, find the closest ToDo by creation time
        if entry.entered_at:
            # Find ToDo created closest to entered_at
            best = None
            best_diff = None
            for todo in todos:
                diff = abs((todo.creation - entry.entered_at).total_seconds())
                if best_diff is None or diff < best_diff:
                    best_diff = diff
                    best = todo.allocated_to
            if best:
                return best

        # Last resort: just use the first ToDo for this lead
        if todos:
            return todos[0].allocated_to

    # Strategy 2: Fall back to lead_owner on the CRM Lead
    lead_owner = frappe.db.get_value("CRM Lead", entry.parent, "lead_owner")
    if lead_owner:
        return lead_owner

    return None
