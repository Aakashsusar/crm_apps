#!/bin/bash

echo "🔧 Fixing Interakt API to accept both parameter names..."

TARGET_FILE="/home/acash/frappe/frappe-bench/apps/crm/crm/integrations/interakt/api.py"

# Backup
cp "$TARGET_FILE" "$TARGET_FILE.backup.params"

# Use sed to update the function signature and add parameter aliasing
sed -i '/^def get_whatsapp_messages(reference_doctype, reference_docname):/,/"""$/ {
    s/def get_whatsapp_messages(reference_doctype, reference_docname):/def get_whatsapp_messages(reference_doctype, reference_docname=None, reference_name=None):/
}' "$TARGET_FILE"

# Add parameter aliasing at the start of the function
sed -i '/def get_whatsapp_messages/,/"""$/ {
    /"""$/a\
	# Handle both parameter names for compatibility\
	if reference_name and not reference_docname:\
		reference_docname = reference_name
}' "$TARGET_FILE"

echo "✅ Updated function to accept both reference_name and reference_docname"
echo ""
echo "🔄 Restart bench:"
echo "   cd ~/frappe/frappe-bench"
echo "   bench restart"
