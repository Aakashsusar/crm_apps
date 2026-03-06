import frappe

def map_fields():
    print("Mapping fields for Ipshopy Seller Hub...")
    try:
        page = frappe.get_doc("Facebook Page", {"page_name": "Ipshopy Seller Hub"})
    except frappe.DoesNotExistError:
        print("Page 'Ipshopy Seller Hub' not found. Ensure forms were fetched.")
        return
        
    forms = frappe.get_all("Facebook Lead Form", filters={"page": page.id})
    print(f"Found {len(forms)} forms.")

    for form_data in forms:
        form = frappe.get_doc("Facebook Lead Form", form_data.name)
        print(f"Form: {form.form_name}")
        
        has_first_name = False
        
        for q in form.questions:
            key = q.key.lower()
            mapped_field = "custom_field_text"
            
            if "name" in key:
                mapped_field = "first_name"
                has_first_name = True
            elif "email" in key:
                mapped_field = "email"
            elif "phone" in key or "mobile" in key:
                mapped_field = "mobile_no"
            elif "company" in key or "organization" in key:
                mapped_field = "organization"
                
            q.mapped_to_crm_field = mapped_field
            print(f"  Mapped {q.label} ({q.key}) -> {mapped_field}")
        
        # fallback: if no name mapping, map the first question to first_name
        if not has_first_name and len(form.questions) > 0:
            form.questions[0].mapped_to_crm_field = "first_name"
            print(f"  Fallback: Mapped {form.questions[0].label} ({form.questions[0].key}) -> first_name")

        form.save(ignore_permissions=True)
        print(f"Saved {form.form_name}")
        
    frappe.db.commit()
    print("Mapping complete.")
