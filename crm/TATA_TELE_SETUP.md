# Tata Teleservices Integration - Setup Guide

## Prerequisites
- Tata Teleservices account
- API credentials (API Endpoint, API Token, Account ID)
- Active phone number registered with Tata Teleservices

## Step-by-Step Setup

### 1. Database Setup (Backend)
The following DocType needs to be created in your Frappe database:

```bash
# Navigate to your Frappe bench directory
cd /home/shubh/frappe/my-bench

# Run bench command to create the new DocType
bench execute crm.hooks.after_install

# Or manually register via Frappe UI:
# Go to Setup → DocType → Create New
# Then sync the database
```

### 2. Configure Tata Teleservices Settings

**Via UI (Recommended)**:
1. Go to **Settings** → **Integrations** → **Telephony**
2. Click on **Tata Teleservices** section
3. Enable the integration: Check the "Enabled" box
4. Fill in the required fields:
   - **API Endpoint**: `https://api-smartflo.tatateleservices.com/v1/click_to_call`
   - **API Token**: Your Tata Teleservices authentication token
   - **Account ID**: Your Tata Teleservices Account ID
   - **Phone Number**: Your default phone number (e.g., +919876543210)
5. Click **Update**

**Via Database**:
```python
# Execute in Frappe console
import frappe

frappe.get_doc({
    'doctype': 'CRM Tata Tele Settings',
    'enabled': 1,
    'api_endpoint': 'https://api-smartflo.tatateleservices.com/v1/click_to_call',
    'api_token': 'YOUR_API_TOKEN',
    'account_id': 'YOUR_ACCOUNT_ID',
    'phone_number': '+919876543210'
}).insert()
```

### 3. Set Default Calling Medium (Optional)
1. Go to **Settings** → **Integrations** → **Telephony**
2. Select **Default medium**: "Tata Tele"
3. Click **Update**

This setting ensures Tata Tele is used by default when making calls. If not set, users will be prompted to choose when multiple services are enabled.

### 4. Test the Connection
To verify API credentials are working:

```python
# Execute in Frappe console
from crm.integrations.tata_tele.handler import validate_connection

result = validate_connection()
print(result)
# Expected output: {'ok': True, 'message': 'Connection successful'}
```

### 5. Make Your First Call
1. Go to any **Contact**, **Lead**, or **Deal**
2. Click the **"Make call"** button next to the mobile number
3. If Tata Tele is enabled and set as default, call will initiate immediately
4. A call popup window will appear with:
   - Contact name and number
   - Call status (Calling, In progress, etc.)
   - Call duration timer
   - Options to add notes or tasks
5. The call log will be automatically created and linked to the record

## Configuration Details

### API Endpoint
- **Default**: `https://api-smartflo.tatateleservices.com/v1/click_to_call`
- **Purpose**: URL where click-to-call API requests are sent
- **Method**: POST
- **Content-Type**: application/json

### Request Format
```json
{
  "from": "+919876543210",
  "to": "+919123456789",
  "account_id": "YOUR_ACCOUNT_ID"
}
```

### Authentication
- **Type**: Bearer Token (HTTP Authorization header)
- **Header**: `Authorization: Bearer YOUR_API_TOKEN`

### Webhook Configuration
To receive real-time call status updates, configure your Tata Teleservices webhook to point to:

```
POST https://yoursite.com/api/method/crm.integrations.tata_tele.handler.webhook_handler
```

The webhook should include the following parameters:
- `call_id` or `id` - Unique call identifier
- `status` or `call_status` - Call status
- `duration` (optional) - Call duration in seconds

## User Permissions

### System Manager
- Can configure Tata Tele settings
- Can modify default calling medium
- Can view all call logs

### Telephony Agent
- Can make calls
- Can view call UI
- Can add notes and tasks to calls
- Cannot modify settings

### Other Users
- If telephony is enabled, can make calls
- Can add notes and tasks

## Troubleshooting

### Issue: "Integration Not Enabled"
**Solution**: Ensure Tata Tele Settings is enabled in Settings → Integrations → Telephony

### Issue: "API Error" when making a call
**Solutions**:
1. Verify API endpoint is correct
2. Check API token hasn't expired
3. Verify Account ID is correct
4. Check phone numbers are in correct format (should include country code)
5. Review logs in Desk → Tools → System Console for detailed errors

### Issue: "Phone Number Missing"
**Solution**: Ensure phone number is configured in Tata Tele Settings

### Issue: Calls not appearing in logs
**Solution**: Check that "Make call" response includes `call_id` field

### Issue: Real-time updates not working
**Solution**: 
1. Verify WebSocket connection is working (check browser console)
2. Ensure webhook is properly configured with Tata Teleservices
3. Check that webhook requests are reaching your server (view request logs)

## Monitoring and Logs

### View Call Logs
1. Go to **CRM** → **Call Log**
2. Filter by "Telephony Medium" = "Tata Tele"
3. View call details, duration, status, linked records

### View Integration Logs
1. Go to **Settings** → **Integration Logs**
2. Filter by "Service Name" = "Tata Tele"
3. Review request/response data for debugging

### Enable Debug Logging
```python
# In Frappe console
frappe.db.set_value('System Settings', None, 'enable_frappe_api_log', 1)
```

## Performance Optimization

1. **Enable caching** for settings:
   - Settings are cached for 24 hours by default
   - No need to query database for every call

2. **Use async webhooks** if handling high call volumes

3. **Configure CDN** for API responses

## API Rate Limits
Check with Tata Teleservices for:
- Calls per minute
- Calls per hour
- Concurrent calls limit

## Support and Documentation

- **Tata Teleservices Docs**: https://cloudphone.tatateleservices.com/docs
- **Frappe CRM Documentation**: https://github.com/frappe/crm
- **Report Issues**: Create an issue in the CRM repository

## Uninstalling the Integration

To completely remove Tata Tele integration:

```bash
# 1. Disable the setting
frappe.db.set_value('CRM Tata Tele Settings', None, 'enabled', 0)

# 2. Delete the DocType (if needed)
frappe.delete_doc('DocType', 'CRM Tata Tele Settings')

# 3. Restart bench
bench restart
```

## Additional Notes

- Call logs are automatically linked to Contact, Lead, or Deal based on phone number matching
- All API calls include request/response logging for audit trail
- Call history is retained as per Frappe's data retention policy
- Integration works across all CRM modules (Lead, Deal, Contact, etc.)
