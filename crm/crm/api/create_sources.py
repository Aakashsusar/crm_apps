import frappe

def create_sources():
    print("Creating Lead Sync Source records...")
    try:
        page = frappe.get_doc("Facebook Page", {"page_name": "Ipshopy Seller Hub"})
    except frappe.DoesNotExistError:
        print("Page 'Ipshopy Seller Hub' not found. Ensure forms were fetched.")
        return

    forms = frappe.get_all("Facebook Lead Form", filters={"page": page.id})
    token = "EAAcLPVZCYckUBQil7xr6ZAIekyHGZAfk1iuls8b1cFkVkjPwCBmsvq4Tf0wfBT7Typi9ZAJdZAQjgyq36AY4itj97AxqU9B8d5HU4fkZBqe3FWuyisZATIyQU6qhUoaJZBzu4dvcHvfmJwI125QtqpfMuA3AZBJ2YZCfOTIJDn9dLDAyWOITZAfvxXVomowFqImqg9n"
    
    for form in forms:
        form_doc = frappe.get_doc("Facebook Lead Form", form.name)
        source_name = f"FB Sync - {form_doc.form_name[:80]}"
        
        sync_source_exists = frappe.db.exists("Lead Sync Source", {"facebook_lead_form": form.name})
        if not sync_source_exists:
            doc = frappe.get_doc({
                "doctype": "Lead Sync Source",
                "name": source_name,
                "type": "Facebook",
                "facebook_page": page.id,
                "facebook_lead_form": form.name,
                "access_token": token,
                "enabled": 1,
                "background_sync_frequency": "Every 2 Minutes"
            })
            doc.insert(ignore_permissions=True)
            print("Created Sync Source for form:", form.name)
        else:
            doc = frappe.get_doc("Lead Sync Source", sync_source_exists)
            doc.background_sync_frequency = "Every 2 Minutes"
            doc.enabled = 1
            doc.access_token = token
            doc.save(ignore_permissions=True)
            print("Updated Sync Source for form:", form.name)
            
    frappe.db.commit()
    print("Done configuring Sync Sources.")
