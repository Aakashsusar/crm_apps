# Interakt Integration for Frappe CRM

This integration allows you to send WhatsApp messages to leads, deals, contacts, and organizations using Interakt's WhatsApp Business API.

## Features

- ✅ Send WhatsApp template messages to leads
- ✅ Automatic welcome message when lead is created
- ✅ Track message delivery status (Sent, Delivered, Read, Failed)
- ✅ Per-user WhatsApp number configuration
- ✅ Message logging and history
- ✅ Webhook support for status updates
- ✅ Integration with CRM activities timeline

## Setup Instructions

### 1. Install Dependencies

```bash
cd frappe-bench
bench --site your-site.localhost migrate
```

### 2. Configure Interakt Settings

1. Go to **CRM Settings** → **Interakt Settings**
2. Check **Enabled**
3. Enter your **API Key** from Interakt dashboard
   - Get it from: https://app.interakt.ai/settings/developer-setting
4. Set **Default Country Code** (default: +91)
5. Optionally enable **Send Welcome Message on Lead Create**
6. Save

### 3. Configure Webhook (Optional)

1. Copy the **Webhook URL** from Interakt Settings
2. Go to your Interakt dashboard
3. Configure the webhook URL to receive delivery status updates

### 4. Configure User WhatsApp Numbers

1. Go to **CRM Settings** → **Telephony Agent**
2. For each user who will send WhatsApp messages:
   - Create/Edit their agent record
   - Check **Enable Interakt**
   - Enter their **WhatsApp Number** (with country code)
   - Save

### 5. Create Templates in Interakt

1. Go to Interakt dashboard: https://app.interakt.ai/templates/list
2. Create your WhatsApp message templates
3. Get approval from WhatsApp
4. Note the template **code name** (used in API calls)

## Usage

### Automatic Welcome Message

When **Send Welcome Message on Lead Create** is enabled:
- A welcome message is automatically sent when a new lead is created
- Uses the `seller_registration` template
- Sends to the lead's phone number
- Includes the lead's name in the message

### Manual Message Sending (Coming Soon)

- Send WhatsApp button in Lead/Deal/Contact pages
- Template selector with preview
- Variable input for template parameters

## Template Structure

The default welcome template (`seller_registration`) has:

**Header:** PDF document (Ipshopy_Policies.pdf)
**Body:** Welcome message with 1 variable ({{1}} = Name)
**Language:** English (en)

Example payload:
```json
{
  "countryCode": "+91",
  "phoneNumber": "9876543210",
  "type": "Template",
  "template": {
    "name": "seller_registration",
    "languageCode": "en",
    "headerValues": ["<PDF_URL>"],
    "fileName": "Ipshopy_Policies.pdf",
    "bodyValues": ["John Doe"]
  }
}
```

## Message Status Tracking

Messages go through these statuses:
- **Pending:** Message created, not yet sent
- **Sent:** Message sent to Interakt
- **Delivered:** Message delivered to recipient
- **Read:** Message read by recipient
- **Failed:** Message delivery failed

## API Endpoints

### Check if Interakt is Enabled
```python
frappe.call('crm.integrations.interakt.api.is_enabled')
```

### Send Welcome Message to Lead
```python
frappe.call({
    method: 'crm.integrations.interakt.api.send_welcome_message_to_lead',
    args: {
        lead_name: 'LEAD-00001'
    }
})
```

### Send Template Message
```python
frappe.call({
    method: 'crm.integrations.interakt.api.send_template_message',
    args: {
        reference_doctype: 'CRM Lead',
        reference_docname: 'LEAD-00001',
        phone_number: '+919876543210',
        template_name: 'seller_registration',
        language_code: 'en',
        header_values: ['<PDF_URL>'],
        body_values: ['John Doe'],
        file_name: 'Ipshopy_Policies.pdf'
    }
})
```

## Troubleshooting

### Messages not sending

1. Check if Interakt is enabled in settings
2. Verify API key is correct
3. Check if lead has a valid phone number
4. Check Error Log for API errors

### Webhook not working

1. Ensure webhook URL is publicly accessible
2. Verify webhook is configured in Interakt dashboard
3. Check Error Log for webhook errors

### Phone number format issues

- Phone numbers should be without country code in the `phone_number` field
- Country code is sent separately
- Example: For +919876543210, send country_code="+91", phone_number="9876543210"

## Files Structure

```
crm/integrations/interakt/
├── __init__.py
├── README.md
├── interakt_handler.py    # Main Interakt API wrapper
├── api.py                 # Frappe API endpoints
├── utils.py               # Helper functions
└── webhooks.py            # Webhook handlers

crm/fcrm/doctype/
├── crm_interakt_settings/      # Settings DocType
├── crm_whatsapp_message/       # Message log DocType
└── crm_telephony_agent/        # Updated with Interakt fields
```

## Support

For issues or questions:
- Check Frappe CRM documentation
- Check Interakt API documentation: https://www.interakt.shop/resource-center/
- Check Error Log in Frappe

## License

Same as Frappe CRM (AGPLv3)
