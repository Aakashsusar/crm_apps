#!/bin/bash

# Script to update Interakt handler with send_text_message method

echo "🔄 Updating Interakt handler in WSL..."

TARGET_FILE="/home/acash/frappe/frappe-bench/apps/crm/crm/integrations/interakt/interakt_handler.py"

# Backup
echo "📦 Creating backup..."
cp "$TARGET_FILE" "$TARGET_FILE.backup.$(date +%Y%m%d_%H%M%S)"

# Check if send_text_message already exists
if grep -q "def send_text_message" "$TARGET_FILE"; then
    echo "✅ send_text_message method already exists!"
else
    echo "➕ Adding send_text_message method..."
    
    # Add the method before the last line of the file
    cat >> "$TARGET_FILE" << 'ENDOFMETHOD'

	def send_text_message(
		self,
		phone_number,
		message_text,
		user_id=None,
		callback_data=None,
	):
		"""
		Send a free text WhatsApp message via Interakt API.
		
		:param phone_number: Full phone number with country code (e.g., +919876543210)
		:param message_text: The text message to send
		:param user_id: Optional user identifier
		:param callback_data: Optional callback data
		:return: Response dict with message_id
		"""
		if not self.api_key:
			frappe.throw(_("Interakt API Key is not configured"))

		# Prepare request payload
		payload = {
			"fullPhoneNumber": phone_number,
			"type": "Text",
			"data": {
				"message": message_text
			}
		}

		# Add optional fields
		if user_id:
			payload["userId"] = user_id

		if callback_data:
			payload["callbackData"] = callback_data

		# Make API request
		url = f"{self.base_url}/public/message/"
		headers = {
			"Authorization": f"Basic {self.api_key}",
			"Content-Type": "application/json",
		}

		try:
			response = requests.post(url, json=payload, headers=headers, timeout=30)
			response.raise_for_status()
			
			result = response.json()
			
			if result.get("result"):
				return {
					"success": True,
					"message_id": result.get("id"),
					"message": result.get("message", "Message sent successfully"),
				}
			else:
				return {
					"success": False,
					"error": result.get("message", "Failed to send message"),
				}
				
		except requests.exceptions.RequestException as e:
			frappe.log_error(
				title="Interakt Text Message Error",
				message=f"Error sending text message: {str(e)}\nPayload: {payload}",
			)
			return {
				"success": False,
				"error": str(e),
			}
ENDOFMETHOD

    echo "✅ Method added successfully!"
fi

echo ""
echo "🔄 Now restart bench:"
echo "   cd ~/frappe/frappe-bench"
echo "   bench restart"
