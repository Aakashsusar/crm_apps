#!/usr/bin/env python3

import re

file_path = "/home/acash/frappe/frappe-bench/apps/crm/crm/integrations/interakt/api.py"

print("🔧 Fixing parameter names in Interakt API...")

with open(file_path, 'r') as f:
    content = f.read()

# Find and replace the function signature and add parameter handling
old_function_start = '''@frappe.whitelist()
def get_whatsapp_messages(reference_doctype, reference_docname):
	"""
	Get all WhatsApp messages for a specific document (Lead/Deal/Contact).
	Returns data in format compatible with frontend WhatsAppArea component.
	
	:param reference_doctype: DocType (e.g., 'CRM Lead')
	:param reference_docname: Document name (e.g., 'LEAD-00001')
	:return: List of messages in frontend-compatible format
	"""
	messages = frappe.get_all('''

new_function_start = '''@frappe.whitelist()
def get_whatsapp_messages(reference_doctype, reference_docname=None, reference_name=None):
	"""
	Get all WhatsApp messages for a specific document (Lead/Deal/Contact).
	Returns data in format compatible with frontend WhatsAppArea component.
	
	:param reference_doctype: DocType (e.g., 'CRM Lead')
	:param reference_docname: Document name (e.g., 'LEAD-00001')
	:param reference_name: Alias for reference_docname (for compatibility)
	:return: List of messages in frontend-compatible format
	"""
	# Handle both parameter names for compatibility
	if reference_name and not reference_docname:
		reference_docname = reference_name
	
	messages = frappe.get_all('''

if old_function_start in content:
    content = content.replace(old_function_start, new_function_start)
    print("✅ Function signature updated")
else:
    print("⚠️  Could not find exact match, trying alternative...")
    # Try a more flexible pattern
    pattern = r'(@frappe\.whitelist\(\)\ndef get_whatsapp_messages\(reference_doctype, reference_docname\):)'
    if re.search(pattern, content):
        content = re.sub(
            r'def get_whatsapp_messages\(reference_doctype, reference_docname\):',
            'def get_whatsapp_messages(reference_doctype, reference_docname=None, reference_name=None):',
            content
        )
        # Add parameter handling after the docstring
        content = re.sub(
            r'("""[\s\S]*?""")\n(\tmessages = frappe\.get_all\()',
            r'\1\n\t# Handle both parameter names for compatibility\n\tif reference_name and not reference_docname:\n\t\treference_docname = reference_name\n\n\2',
            content
        )
        print("✅ Function updated with regex")
    else:
        print("❌ Could not find function")

with open(file_path, 'w') as f:
    f.write(content)

print("✅ File saved!")
print("\n🔄 Now run: bench restart")
