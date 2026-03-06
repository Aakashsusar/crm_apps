
import frappe
from crm.api.whatsapp import create_whatsapp_message
from crm.integrations.interakt.api import get_whatsapp_messages

def verify():
    # 1. Setup Lead
    lead_name = "Dr Acash Sus"
    phone = "8411094680"
    
    # Check if lead exists
    leads = frappe.get_all("CRM Lead", filters={"mobile_no": ["like", f"%{phone}%"]}, limit=1)
    
    if not leads:
        print(f"Creating new lead: {lead_name}")
        lead = frappe.get_doc({
            "doctype": "CRM Lead",
            "first_name": "Dr Acash",
            "last_name": "Sus",
            "mobile_no": phone,
            "status": "Lead" # Adjust status if needed
        })
        lead.insert(ignore_permissions=True)
        lead_id = lead.name
    else:
        lead_id = leads[0].name
        print(f"Found existing lead: {lead_id}")

    # 2. Simulate Frontend Call (Sending Message)
    print(f"Attempting to send message to {lead_id} ({phone})...")
    msg_content = "Hello from backend verification! 🧪"
    
    try:
        # Expected signature: create_whatsapp_message(reference_doctype, reference_name, message, to, attach, reply_to, content_type)
        # Frontend calls this.
        message_id = create_whatsapp_message(
            reference_doctype="CRM Lead",
            reference_name=lead_id,
            message=msg_content,
            to=phone,
            attach=None,
            reply_to=None,
            content_type="text"
        )
        print(f"✅ API Call Successful! Message ID/Name: {message_id}")
        
    except Exception as e:
        print(f"❌ API Call Failed!")
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return

    # 3. Verify DB Entry
    print("Verifying database entry...")
    # The API might accept it but fail later? 
    # Actually create_whatsapp_message calls send_text_message_to_lead which calls Interakt,
    # so if it returns, it means Interakt accepted it (or we caught the error).
    
    # Check "CRM WhatsApp Message"
    msgs = frappe.get_all("CRM WhatsApp Message", 
                         filters={"reference_docname": lead_id}, 
                         order_by="creation desc", 
                         limit=5)
    
    found = False
    for m in msgs:
        doc = frappe.get_doc("CRM WhatsApp Message", m.name)
        if doc.message_content == msg_content:
            print(f"✅ Found message in DB: {doc.name}")
            print(f"   Status: {doc.status}")
            print(f"   Phone Cleaned: {doc.phone_number}") # Should be cleaned
            found = True
            break
            
    if not found:
        print("❌ Message not found in DB immediately (might be async or failed silently?)")
    
    # 4. Check Frontend Data Format
    print("Checking get_whatsapp_messages (Frontend Data)...")
    frontend_msgs = get_whatsapp_messages("CRM Lead", lead_id)
    if frontend_msgs:
        print(f"✅ Frontend will see {len(frontend_msgs)} messages.")
        # Check the last one
        last = frontend_msgs[-1]
        print(f"   Last message: {last.get('message')}")
        if last.get('message') == msg_content:
             print("   Matches sent message.")
    else:
        print("⚠️ No messages returned for frontend.")

if __name__ == "__main__":
    verify()
