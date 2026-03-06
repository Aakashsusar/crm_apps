#!/bin/bash

echo "🔧 Fixing parameter mismatch in whatsapp.py..."

TARGET_FILE="/home/acash/frappe/frappe-bench/apps/crm/crm/api/whatsapp.py"

# Backup
cp "$TARGET_FILE" "$TARGET_FILE.backup.param_fix"

# Fix the get_whatsapp_messages function to handle both parameter names
python3 << 'PYTHON_EOF'
import re

file_path = "/home/acash/frappe/frappe-bench/apps/crm/crm/api/whatsapp.py"

with open(file_path, 'r') as f:
    content = f.read()

# Find and replace the get_whatsapp_messages routing
old_pattern = r'''# Check if Interakt integration is enabled
	interakt_enabled = frappe\.db\.get_single_value\("CRM Interakt Settings", "enabled"\)
	if interakt_enabled:
		# Use Interakt integration
		from crm\.integrations\.interakt\.api import get_whatsapp_messages as get_interakt_messages
		return get_interakt_messages\(reference_doctype, reference_name\)'''

new_code = '''# Check if Interakt integration is enabled
	interakt_enabled = frappe.db.get_single_value("CRM Interakt Settings", "enabled")
	if interakt_enabled:
		# Use Interakt integration
		from crm.integrations.interakt.api import get_whatsapp_messages as get_interakt_messages
		return get_interakt_messages(reference_doctype, reference_name)'''

content = re.sub(old_pattern, new_code, content)

with open(file_path, 'w') as f:
    f.write(content)

print("✅ File updated!")
PYTHON_EOF

echo ""
echo "🔄 Now restart bench:"
echo "   cd ~/frappe/frappe-bench"
echo "   bench restart"
