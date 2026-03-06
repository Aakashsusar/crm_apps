import frappe
from frappe import _, msgprint
from frappe.utils import now_datetime
import requests

def run():
    page_name = "Ipshopy Seller Hub"
    # Find the page
    page = frappe.get_all("Facebook Page", filters={"page_name": page_name}, fields=["name", "access_token", "id"])
    if not page:
        print(f"Page {page_name} not found.")
        return
        
    page = page[0]
    page_id = page.id
    access_token = page.access_token
    
    sync_forms(page.name, page_id, access_token)

def sync_forms(page_docname, page_id, access_token):
    print(f"Syncing forms for page {page_id}...")
    url = f"https://graph.facebook.com/v23.0/{page_id}/leadgen_forms"
    params = {
        "access_token": access_token,
        "fields": "name,id,questions",
        "limit": "100"
    }
    
    response = requests.get(url, params=params)
    if response.status_code != 200:
        print(f"Failed to fetch forms: {response.text}")
        return
        
    data = response.json()
    forms = data.get("data", [])
    
    print(f"Found {len(forms)} forms.")
    
    for fb_form in forms:
        form_id = fb_form.get("id")
        form_name = fb_form.get("name")
        questions = fb_form.get("questions", [])
        
        print(f"Processing form {form_name} ({form_id}) with {len(questions)} questions")
        
        # Check if form exists
        exists = frappe.db.exists("Facebook Lead Form", {"id": form_id})
        if not exists:
            doc = frappe.new_doc("Facebook Lead Form")
            doc.id = form_id
            doc.form_name = form_name
            doc.page = page_docname
            doc.save(ignore_permissions=True)
            print(f"Created new form {form_id}")
            parent_name = doc.name
        else:
            doc = frappe.get_doc("Facebook Lead Form", exists)
            doc.form_name = form_name
            doc.page = page_docname
            doc.save(ignore_permissions=True)
            parent_name = doc.name
            
        sync_questions(parent_name, questions)

def sync_questions(parent_name, questions):
    # Get existing questions to avoid duplicates
    existing_questions = frappe.get_all("Facebook Lead Form Question", filters={"parent": parent_name}, fields=["name", "id"])
    existing_map = {q.id: q.name for q in existing_questions if q.id}
    
    doc = frappe.get_doc("Facebook Lead Form", parent_name)
    
    for q in questions:
        q_id = q.get("id")
        q_type = q.get("type", "")
        q_key = q.get("key", "")
        q_label = q.get("label", "")
        
        # Determine CRM Mapping
        mapped_to = None
        if q_type == "FULL_NAME":
            mapped_to = "lead_name"
        elif q_type == "PHONE":
            mapped_to = "mobile_no"
        elif q_type == "EMAIL":
            mapped_to = "email"
        elif q_type == "CITY":
            mapped_to = "city"
            
            # Additional keys mapping based on typical CRM Lead fields
            # Add custom text for fields without direct mapping
        
        if q_id in existing_map:
            # Update
            row = doc.get("questions", {"id": q_id})
            if row:
                row[0].type = q_type
                row[0].key = q_key
                row[0].label = q_label
                if mapped_to and not row[0].mapped_to_crm_field:
                    row[0].mapped_to_crm_field = mapped_to
        else:
            # Add new
            row = doc.append("questions", {})
            row.id = q_id
            row.type = q_type
            row.key = q_key
            row.label = q_label
            if mapped_to:
                row.mapped_to_crm_field = mapped_to
                
    doc.save(ignore_permissions=True)
    frappe.db.commit()

