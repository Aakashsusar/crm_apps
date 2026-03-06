# 📱 Interakt WhatsApp Integration for Frappe CRM

Automatically send WhatsApp messages to leads using Interakt's WhatsApp Business API.

---

## 🚀 Quick Start

### 1. Run Installation Script

**Linux/Mac:**
```bash
cd ~/frappe-bench/apps/crm
bash install_interakt.sh
```

**Windows (PowerShell):**
```powershell
cd ~/frappe-bench/apps/crm
.\install_interakt.ps1
```

### 2. Configure Settings

1. Open CRM → Search "CRM Interakt Settings"
2. Enable Interakt
3. Add your API Key from [Interakt Dashboard](https://app.interakt.ai/settings/developer-setting)
4. Save

### 3. Test

Create a new lead with a phone number and check if the WhatsApp message is sent!

---

## 📖 Documentation

| Document | Description |
|----------|-------------|
| [QUICK_INSTALL.md](QUICK_INSTALL.md) | Quick installation guide |
| [INTERAKT_SETUP_GUIDE.md](INTERAKT_SETUP_GUIDE.md) | Detailed setup instructions |
| [INTERAKT_IMPLEMENTATION_SUMMARY.md](INTERAKT_IMPLEMENTATION_SUMMARY.md) | Technical implementation details |
| [INTERAKT_DEPLOYMENT_CHECKLIST.md](INTERAKT_DEPLOYMENT_CHECKLIST.md) | Production deployment checklist |

---

## ✨ Features

- ✅ Automatic welcome message when lead is created
- ✅ Message delivery tracking (Sent → Delivered → Read)
- ✅ Webhook support for real-time status updates
- ✅ Per-user WhatsApp number configuration
- ✅ Comprehensive error logging
- ✅ Phone number format handling

---

## 🎯 What Gets Installed

### DocTypes:
1. **CRM Interakt Settings** - Configuration
2. **CRM WhatsApp Message** - Message logs
3. **CRM Telephony Agent** - Updated with Interakt fields

### Integration:
- Automatic welcome message on lead creation
- Uses `seller_registration` template
- Sends PDF attachment (Ipshopy_Policies.pdf)
- Includes lead's full name

---

## 🧪 Testing

Run the test script:
```bash
bench --site your-site.localhost console
```
```python
from crm.integrations.interakt.test_integration import test_integration
test_integration()
```

Create a test lead:
```python
from crm.integrations.interakt.test_integration import create_test_lead
create_test_lead()
```

---

## 📋 Manual Installation

If the script doesn't work, follow these steps:

```bash
cd ~/frappe-bench

# 1. Migrate
bench --site your-site.localhost migrate

# 2. Clear cache
bench --site your-site.localhost clear-cache

# 3. Restart
bench restart
```

Then configure settings at: `http://your-site.localhost:8000/app/crm-interakt-settings`

---

## 🔧 Configuration

### Required Settings:
- ✅ **Enabled**: Check to enable integration
- 🔑 **API Key**: From Interakt dashboard
- 🌍 **Default Country Code**: e.g., +91 for India

### Optional Settings:
- 📧 **Send Welcome Message on Lead Create**: Auto-send welcome message
- 🔗 **Webhook URL**: For status updates (auto-generated)

---

## 📊 Message Flow

1. **Lead Created** → Hook triggers
2. **Extract Data** → Get phone number and name
3. **Send Message** → Call Interakt API
4. **Log Message** → Create WhatsApp Message record
5. **Track Status** → Update via webhooks (Sent → Delivered → Read)

---

## 🐛 Troubleshooting

### Can't find CRM Interakt Settings?

```bash
# Clear cache and restart
bench --site your-site.localhost clear-cache
bench restart
```

### Messages not sending?

1. Check if Interakt is enabled
2. Verify API key is correct
3. Ensure lead has a phone number
4. Check Error Log for details

### Phone number format issues?

Phone numbers are automatically cleaned and formatted. Supported formats:
- `+919876543210` ✓
- `9876543210` ✓
- `+91 98765 43210` ✓

---

## 📞 Support

- **Interakt API Docs**: https://www.interakt.shop/resource-center/
- **Frappe CRM**: https://discuss.frappe.io/c/frappe-crm
- **Error Logs**: Check in Frappe → Error Log

---

## 📝 Template Structure

The default `seller_registration` template includes:

- **Header**: PDF document (Ipshopy_Policies.pdf)
- **Body**: Welcome message with variable `{{1}}` = Lead Name
- **Language**: English (en)

---

## 🎉 Success!

Once configured, every new lead will automatically receive a WhatsApp welcome message!

**Happy messaging!** 🚀
