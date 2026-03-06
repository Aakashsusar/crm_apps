import frappe


def execute():
    """Add call_status field to User doctype"""
    # Check if field already exists
    if not frappe.db.exists("Custom Field", {"dt": "User", "fieldname": "call_status"}):
        # Create custom field for call status
        call_status_field = {
            "doctype": "Custom Field",
            "dt": "User",
            "fieldname": "call_status",
            "fieldtype": "Select",
            "label": "Call Status",
            "options": "Available\nBusy\nIn Call\nDo Not Disturb",
            "default": "Available",
            "insert_after": "mobile_no",
            "description": "Current call availability status for call routing"
        }
        
        frappe.get_doc(call_status_field).insert()
        frappe.db.commit()
        print("Added call_status field to User doctype")
    else:
        print("call_status field already exists")