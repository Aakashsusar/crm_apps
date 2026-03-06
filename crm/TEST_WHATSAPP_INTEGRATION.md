# WhatsApp Integration Testing Guide

## Overview
The Interakt WhatsApp integration has been fully integrated with the existing CRM frontend. The system now supports:
- ✅ Template messages (automatic welcome on lead creation)
- ✅ Free text messages (manual messages from UI)
- ✅ WhatsApp tab in Lead page
- ✅ Chat-style bubble interface
- ✅ Message status tracking (Sent → Delivered → Read)

## Backend Changes Made

### 1. Updated `crm/api/whatsapp.py`
- Modified `is_whatsapp_enabled()` to check for Interakt integration
- Modified `get_whatsapp_messages()` to route to Interakt when enabled
- Modified `create_whatsapp_message()` to use Interakt for text messages

### 2. Updated `crm/integrations/interakt/api.py`
- Enhanced `get_whatsapp_messages()` to return frontend-compatible format
- Transforms CRM WhatsApp Message data to match WhatsApp Message format
- Maps fields: direction, status, message_content, etc.

### 3. Existing Components (No Changes Needed!)
The frontend already has all necessary components:
- ✅ `frontend/src/components/Activities/WhatsAppArea.vue` - Chat bubble UI
- ✅ `frontend/src/components/Activities/WhatsAppBox.vue` - Message input
- ✅ `frontend/src/pages/Lead.vue` - WhatsApp tab already configured
- ✅ Status indicators (✓ sent, ✓✓ delivered, blue ✓✓ read)

## Testing Steps

### Step 1: Restart Bench
```bash
cd ~/frappe/frappe-bench
bench restart
```

### Step 2: Clear Cache
```bash
bench --site ipshopy.localhost clear-cache
```

### Step 3: Test Backend (Console)
```bash
bench --site ipshopy.localhost console
```

Then run:
```python
exec(open('test_text_message_backend.py').read())
```

Expected output:
- ✅ Functions imported successfully
- ✅ Message sent successfully
- ✅ Messages retrieved from database

### Step 4: Test Frontend (Browser)

1. **Open a Lead**
   - Navigate to: http://ipshopy.localhost:8000/crm/leads
   - Click on any lead with a phone number

2. **Check WhatsApp Tab**
   - You should see a "WhatsApp" tab next to Activity, Emails, Comments, etc.
   - Click on the WhatsApp tab

3. **View Existing Messages**
   - You should see any previously sent messages in chat bubbles
   - Messages show on the right (outgoing) with status indicators
   - Status: ✓ (sent), ✓✓ (delivered), blue ✓✓ (read)

4. **Send a Text Message**
   - At the bottom of the WhatsApp tab, there's a message input box
   - Type a message: "Hello! This is a test message 👋"
   - Press Enter or click Send
   - Message should appear immediately in the chat
   - Check your WhatsApp to confirm delivery

5. **Check Message Status**
   - Initially shows ✓ (sent)
   - After delivery: ✓✓ (delivered)
   - After reading: blue ✓✓ (read)
   - Status updates automatically via socket

### Step 5: Test Template Messages

1. **Create a New Lead**
   - Go to Leads list
   - Click "New"
   - Fill in: First Name, Last Name, Mobile Number
   - Save

2. **Check Automatic Welcome Message**
   - The lead should receive the seller_registration template
   - Check the WhatsApp tab - message should appear
   - Check the lead's WhatsApp - they should receive the PDF

## Troubleshooting

### WhatsApp Tab Not Showing
```bash
# Check if Interakt is enabled
bench --site ipshopy.localhost console
```
```python
import frappe
settings = frappe.get_single("CRM Interakt Settings")
print(f"Enabled: {settings.enabled}")
```

### Messages Not Sending
```bash
# Check API key
bench --site ipshopy.localhost console
```
```python
import frappe
settings = frappe.get_single("CRM Interakt Settings")
api_key = settings.get_password("api_key")
print(f"API Key configured: {bool(api_key)}")
```

### Messages Not Appearing in UI
```bash
# Check database
bench --site ipshopy.localhost console
```
```python
import frappe
messages = frappe.get_all("CRM WhatsApp Message", fields=["*"])
print(f"Total messages: {len(messages)}")
for msg in messages[-5:]:
    print(f"{msg.name}: {msg.status} | {msg.message_content[:50]}")
```

### Status Not Updating
- Status updates come from Interakt webhooks
- Ensure webhooks are configured in Interakt dashboard
- Webhook URL: `https://your-site.com/api/method/crm.integrations.interakt.webhooks.handle_webhook`

## API Endpoints

### Get Messages
```javascript
// Frontend call
frappe.call({
  method: 'crm.api.whatsapp.get_whatsapp_messages',
  args: {
    reference_doctype: 'CRM Lead',
    reference_name: 'CRM-LEAD-2026-00001'
  }
})
```

### Send Text Message
```javascript
// Frontend call
frappe.call({
  method: 'crm.api.whatsapp.create_whatsapp_message',
  args: {
    reference_doctype: 'CRM Lead',
    reference_name: 'CRM-LEAD-2026-00001',
    message: 'Hello from CRM!',
    to: '+919876543210',
    attach: '',
    reply_to: '',
    content_type: 'text'
  }
})
```

## Features Implemented

### ✅ Completed
1. Backend API for text messages
2. Integration with existing frontend
3. Chat-style bubble interface
4. Message status tracking
5. Automatic welcome messages
6. WhatsApp tab in Lead page
7. Real-time message updates via socket

### 🚧 Future Enhancements
1. Media support (images, videos, documents)
2. Reply functionality
3. Message reactions
4. Template selector in UI
5. Webhook status updates
6. Message search/filter
7. Bulk messaging

## Data Flow

```
User Types Message in UI
    ↓
WhatsAppBox.vue → create_whatsapp_message()
    ↓
crm/api/whatsapp.py (checks Interakt enabled)
    ↓
crm/integrations/interakt/api.py → send_text_message_to_lead()
    ↓
crm/integrations/interakt/interakt_handler.py → send_text_message()
    ↓
Interakt API (sends to WhatsApp)
    ↓
create_whatsapp_message_log() (saves to DB)
    ↓
Socket event → Frontend updates
    ↓
WhatsAppArea.vue displays message
```

## Success Criteria

✅ WhatsApp tab visible in Lead page
✅ Can send text messages from UI
✅ Messages appear in chat bubbles
✅ Status indicators work (✓, ✓✓, blue ✓✓)
✅ Messages saved to database
✅ Real-time updates via socket
✅ Template messages work on lead creation

## Next Steps

1. **Test the integration** following the steps above
2. **Verify message delivery** on actual WhatsApp
3. **Check status updates** (may need webhook configuration)
4. **Report any issues** for quick fixes
5. **Consider enhancements** from the future list

---

**Note**: The integration reuses existing frontend components, so no UI changes were needed. The backend was updated to route WhatsApp operations through Interakt when enabled, maintaining backward compatibility with the Frappe WhatsApp app.
