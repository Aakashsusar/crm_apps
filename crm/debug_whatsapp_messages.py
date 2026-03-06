"""
Debug script to check WhatsApp message logging
Run this from bench console to diagnose the issue
"""

import frappe

def debug_whatsapp_messages():
    print("\n" + "="*60)
    print("🔍 DEBUGGING WHATSAPP MESSAGE LOGGING")
    print("="*60 + "\n")
    
    # Check 1: Does DocType exist?
    print("1️⃣  Checking if DocType exists...")
    doctype_exists = frappe.db.exists("DocType", "CRM WhatsApp Message")
    if doctype_exists:
        print("   ✅ CRM WhatsApp Message DocType exists")
    else:
        print("   ❌ CRM WhatsApp Message DocType NOT FOUND!")
        print("   💡 Run: bench --site ipshopy.localhost migrate")
        return
    
    # Check 2: Count messages
    print("\n2️⃣  Checking message count...")
    try:
        count = frappe.db.count("CRM WhatsApp Message")
        print(f"   📊 Total messages in database: {count}")
        
        if count == 0:
            print("   ⚠️  No messages found in database")
        else:
            print(f"   ✅ Found {count} message(s)")
    except Exception as e:
        print(f"   ❌ Error counting messages: {e}")
    
    # Check 3: Try to get all messages
    print("\n3️⃣  Fetching all messages...")
    try:
        messages = frappe.get_all(
            "CRM WhatsApp Message",
            fields=["name", "phone_number", "status", "template_name", "creation", "message_id"],
            limit=10
        )
        
        if messages:
            print(f"   ✅ Found {len(messages)} message(s):")
            for msg in messages:
                print(f"   - {msg.name}: {msg.phone_number} | {msg.status} | {msg.template_name}")
        else:
            print("   ⚠️  No messages returned from query")
    except Exception as e:
        print(f"   ❌ Error fetching messages: {e}")
    
    # Check 4: Check Error Log
    print("\n4️⃣  Checking Error Log for WhatsApp errors...")
    try:
        errors = frappe.get_all(
            "Error Log",
            filters={
                "error": ["like", "%WhatsApp%"]
            },
            fields=["name", "error", "creation"],
            order_by="creation desc",
            limit=5
        )
        
        if errors:
            print(f"   ⚠️  Found {len(errors)} error(s):")
            for err in errors:
                print(f"   - {err.name}: {err.creation}")
                print(f"     {err.error[:100]}...")
        else:
            print("   ✅ No WhatsApp-related errors found")
    except Exception as e:
        print(f"   ❌ Error checking error log: {e}")
    
    # Check 5: Check Interakt errors
    print("\n5️⃣  Checking Error Log for Interakt errors...")
    try:
        errors = frappe.get_all(
            "Error Log",
            filters={
                "error": ["like", "%Interakt%"]
            },
            fields=["name", "error", "creation"],
            order_by="creation desc",
            limit=5
        )
        
        if errors:
            print(f"   ⚠️  Found {len(errors)} error(s):")
            for err in errors:
                print(f"   - {err.name}: {err.creation}")
                print(f"     {err.error[:200]}...")
        else:
            print("   ✅ No Interakt-related errors found")
    except Exception as e:
        print(f"   ❌ Error checking error log: {e}")
    
    # Check 6: Test creating a message manually
    print("\n6️⃣  Testing manual message creation...")
    try:
        test_doc = frappe.get_doc({
            "doctype": "CRM WhatsApp Message",
            "message_id": "test_" + frappe.generate_hash(length=10),
            "phone_number": "9999999999",
            "country_code": "+91",
            "template_name": "test_template",
            "template_language": "en",
            "status": "Sent",
            "direction": "Outgoing",
            "reference_doctype": "CRM Lead",
            "reference_docname": "TEST-LEAD",
            "sent_by": frappe.session.user,
        })
        test_doc.insert(ignore_permissions=True)
        frappe.db.commit()
        print(f"   ✅ Test message created: {test_doc.name}")
        
        # Try to fetch it
        fetched = frappe.get_doc("CRM WhatsApp Message", test_doc.name)
        print(f"   ✅ Test message fetched successfully")
        
        # Delete test message
        frappe.delete_doc("CRM WhatsApp Message", test_doc.name, ignore_permissions=True)
        frappe.db.commit()
        print(f"   ✅ Test message deleted")
        
    except Exception as e:
        print(f"   ❌ Error creating test message: {e}")
        import traceback
        traceback.print_exc()
    
    # Check 7: Check recent leads
    print("\n7️⃣  Checking recent leads...")
    try:
        leads = frappe.get_all(
            "CRM Lead",
            fields=["name", "lead_name", "mobile_no", "creation"],
            order_by="creation desc",
            limit=5
        )
        
        if leads:
            print(f"   📋 Found {len(leads)} recent lead(s):")
            for lead in leads:
                print(f"   - {lead.name}: {lead.lead_name} | {lead.mobile_no}")
        else:
            print("   ⚠️  No leads found")
    except Exception as e:
        print(f"   ❌ Error fetching leads: {e}")
    
    print("\n" + "="*60)
    print("✅ DEBUG COMPLETE")
    print("="*60 + "\n")


if __name__ == "__main__":
    debug_whatsapp_messages()
