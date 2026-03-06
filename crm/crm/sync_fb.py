import frappe

def map_fields():
    print("Mapping fields for Ipshopy Seller Hub...")
    # Get the page
    page = frappe.get_doc("Facebook Page", {"page_name": "Ipshopy Seller Hub"})
    
    # Get all forms for this page
    forms = frappe.get_all("Facebook Lead Form", filters={"page": page.id})
    print(f"Found {len(forms)} forms.")
    
    # Check if 'custom_field_text' exists in CRM Lead
    meta = frappe.get_meta("CRM Lead")
    fieldnames = [f.fieldname for f in meta.fields]
    if "custom_field_text" not in fieldnames:
        print("custom_field_text not found in CRM Lead, creating it...")
        custom_field = frappe.get_doc({
            "doctype": "Custom Field",
            "dt": "CRM Lead",
            "fieldname": "custom_field_text",
            "label": "Custom Field Text",
            "fieldtype": "Small Text",
            "insert_after": "mobile_no"
        })
        custom_field.insert(ignore_permissions=True)
        frappe.db.commit()
        print("Created Custom Field.")

    # Mapping Logic
    # Email -> email, Full Name -> first_name (or lead_name), Phone number -> mobile_no
    # We map common strings to actual fields. If not found, use `custom_field_text`
    
    for form_data in forms:
        form = frappe.get_doc("Facebook Lead Form", form_data.name)
        print(f"Form: {form.form_name}")
        for q in form.questions:
            label = q.label.lower()
            key = q.key.lower()
            
            mapped_field = "custom_field_text" # default
            
            if "name" in key:
                mapped_field = "first_name"
            if "email" in key:
                mapped_field = "email"
            if "phone" in key or "mobile" in key:
                mapped_field = "mobile_no"
            if "company" in key or "organization" in key:
                mapped_field = "organization"
                
            q.mapped_to_crm_field = mapped_field
            print(f"  Mapped {q.label} ({q.key}) -> {mapped_field}")
        
        form.save(ignore_permissions=True)
        print(f"Saved {form.form_name}")
        
    frappe.db.commit()
    print("Mapping complete.")
