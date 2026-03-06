# 🚀 Interakt Integration Setup Guide for Frappe CRM

## ✅ What Has Been Implemented

I've successfully integrated Interakt WhatsApp messaging into your Frappe CRM. Here's what's ready:

### Backend Components ✓
1. **Interakt Handler** (`crm/integrations/interakt/interakt_handler.py`)
   - Send template messages
   - User tracking API
   - Event tracking API
   - Error handling and logging

2. **API Endpoints** (`crm/integrations/interakt/api.py`)
   - `is_enabled()` - Check if Interakt is enabled
   - `send_welcome_message_to_lead()` - Send welcome message
   - `send_template_message()` - Send any template message
   - `get_message_status()` - Get message delivery status

3. **Webhook Handler** (`crm/integrations/interakt/webhooks.py`)
   - Receive delivery status updates
   - Update message logs automatically
   - Real-time status updates

4. **Utility Functions** (`crm/integrations/interakt/utils.py`)
   - Phone number cleaning and formatting
   - Country code extraction
   - Lead data helpers

### DocTypes ✓
1. **CRM Interakt Settings** (Single DocType)
   - Enable/disable integration
   - API key configuration
   - Default country code
   - Auto-send welcome message toggle
   - Webhook URL (auto-generated)

2. **CRM WhatsApp Message** (DocType)
   - Message logging
   - Status tracking (Pending → Sent → Delivered → Read)
   - Link to Lead/Deal/Contact/Organization
   - Template details
   - Timestamps for all status changes

3. **CRM Telephony Agent** (Updated)
   - Added Interakt enable checkbox
   - Added WhatsApp number field
   - Per-user configuration

### Automation ✓
- **Automatic Welcome Message**: When a new lead is created, automatically sends the `seller_registration` template with:
  - Lead's full name (First Name + Last Name)
  - PDF attachment (Ipshopy_Policies.pdf)
  - Tracked in WhatsApp Message log

---

## 📋 Installation Steps

### Step 1: Migrate Database

```bash
cd ~/frappe-bench
bench --site your-site.localhost migrate
```

This will create the new DocTypes:
- CRM Interakt Settings
- CRM WhatsApp Message
- Update CRM Telephony Agent

### Step 2: Configure Interakt Settings

1. Open your Frappe CRM
2. Go to **Search Bar** (Ctrl+K) → Type "CRM Interakt Settings"
3. Click on **CRM Interakt Settings**
4. Configure:
   - ✅ Check **Enabled**
   - 🔑 Enter your **API Key** from Interakt
     - Get it from: https://app.interakt.ai/settings/developer-setting
   - 🌍 Set **Default Country Code** (e.g., +91 for India)
   - 📧 Check **Send Welcome Message on Lead Create** (if you want automatic messages)
5. Click **Save**

### Step 3: Configure User WhatsApp Numbers (Optional)

If you want specific users to have their own WhatsApp numbers:

1. Go to **Search Bar** → Type "CRM Telephony Agent"
2. Click **New** or edit existing agent
3. Select **User**
4. In the **Interakt (WhatsApp)** section:
   - ✅ Check **Enable Interakt**
   - 📱 Enter **WhatsApp Number** (with country code, e.g., +919876543210)
5. Click **Save**

### Step 4: Test the Integration

#### Test 1: Create a Lead

1. Go to **Leads** → Click **New**
2. Fill in:
   - **First Name**: Test
   - **Last Name**: User
   - **Phone** or **Mobile No**: 9876543210 (your test number)
3. Click **Save**

**Expected Result:**
- A WhatsApp message should be sent automatically
- Check **Error Log** for any issues
- Check **CRM WhatsApp Message** list to see the message log

#### Test 2: Check Message Status

1. Go to **Search Bar** → Type "CRM WhatsApp Message"
2. You should see the sent message with:
   - Status: Sent (initially)
   - Phone Number
   - Template Name: seller_registration
   - Reference: Link to the lead

---

## 🔧 Configuration Details

### Your Template Structure

Based on your requirements, the `seller_registration` template is configured as:

```json
{
  "countryCode": "+91",
  "phoneNumber": "9876543210",
  "type": "Template",
  "template": {
    "name": "seller_registration",
    "languageCode": "en",
    "headerValues": [
      "https://interaktprodmediastorage.blob.core.windows.net/.../Ipshopy_Policies.pdf"
    ],
    "fileName": "Ipshopy_Policies.pdf",
    "bodyValues": ["{{Lead Name}}"]
  }
}
```

**Variables:**
- `{{1}}` in template body = Lead's Full Name (First Name + Last Name)

### Webhook Configuration (Optional)

For real-time status updates:

1. Copy the **Webhook URL** from CRM Interakt Settings
2. Go to Interakt Dashboard
3. Navigate to Webhooks settings
4. Add the webhook URL
5. Select events: Message Sent, Delivered, Read, Failed

---

## 🧪 Testing Checklist

- [ ] Migrate database successfully
- [ ] CRM Interakt Settings created
- [ ] API Key configured
- [ ] Create a test lead with phone number
- [ ] Check if message appears in CRM WhatsApp Message list
- [ ] Verify message received on WhatsApp
- [ ] Check message status updates (Sent → Delivered → Read)

---

## 🐛 Troubleshooting

### Issue: Messages not sending

**Check:**
1. Is Interakt enabled in settings? ✓
2. Is API key correct? ✓
3. Does lead have a valid phone number? ✓
4. Check **Error Log** (Search Bar → "Error Log")

**Common Errors:**
- "Interakt is not enabled" → Enable in settings
- "Lead does not have a phone number" → Add phone/mobile to lead
- "API Key is not configured" → Add API key in settings

### Issue: Phone number format errors

**Solution:**
- Phone numbers are automatically cleaned (removes spaces, dashes)
- Country code is extracted if present
- Default country code is used if not present

**Examples:**
- `+919876543210` → country_code: +91, phone: 9876543210 ✓
- `9876543210` → country_code: +91 (default), phone: 9876543210 ✓
- `+91 98765 43210` → cleaned to: +91, 9876543210 ✓

### Issue: Webhook not working

**Check:**
1. Is your site publicly accessible?
2. Is webhook URL configured in Interakt dashboard?
3. Check **Error Log** for webhook errors

---

## 📊 Monitoring

### View Sent Messages

1. Go to **CRM WhatsApp Message** list
2. Filter by:
   - Status (Sent, Delivered, Read, Failed)
   - Reference DocType (CRM Lead, CRM Deal, etc.)
   - Date range

### View Message Details

Click on any message to see:
- Message ID (from Interakt)
- Phone number
- Template used
- Status with timestamps
- Linked Lead/Deal/Contact
- Error message (if failed)

---

## 🎯 Next Steps (Phase 2 - Not Implemented Yet)

These features can be added later:

1. **Frontend UI**
   - "Send WhatsApp" button in Lead/Deal pages
   - Template selector modal
   - Variable input form
   - Message preview

2. **Template Management**
   - Fetch templates from Interakt API
   - Template preview in CRM
   - Template variable mapping

3. **Advanced Features**
   - Two-way messaging
   - Conversation threading
   - Campaign tracking
   - Bulk messaging

---

## 📞 Support

If you encounter any issues:

1. Check **Error Log** in Frappe
2. Check Interakt API logs in their dashboard
3. Verify API key and permissions
4. Check phone number format

---

## ✨ Summary

You now have:
- ✅ Interakt integration installed
- ✅ Automatic welcome messages for new leads
- ✅ Message logging and tracking
- ✅ Webhook support for status updates
- ✅ Per-user WhatsApp number configuration

**Ready to test!** Create a new lead and watch the magic happen! 🎉
