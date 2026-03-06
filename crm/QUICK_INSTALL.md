# 🚀 Quick Installation Guide

## Choose Your Method:

### **Method 1: Automated Script (Recommended)**

#### For Linux/Mac:
```bash
cd ~/frappe-bench/apps/crm
bash install_interakt.sh
```

#### For Windows (PowerShell):
```powershell
cd ~/frappe-bench/apps/crm
.\install_interakt.ps1
```

---

### **Method 2: Manual Installation**

#### Step 1: Navigate to Bench Directory
```bash
cd ~/frappe-bench
```

#### Step 2: Run Migration
```bash
bench --site your-site.localhost migrate
```

**Expected Output:**
```
Migrating your-site.localhost
Executing crm.patches...
Installing CRM Interakt Settings
Installing CRM WhatsApp Message
Updating CRM Telephony Agent
Migration complete
```

#### Step 3: Clear Cache
```bash
bench --site your-site.localhost clear-cache
bench --site your-site.localhost clear-website-cache
```

#### Step 4: Restart Services
```bash
bench restart
```

#### Step 5: Verify Installation
```bash
bench --site your-site.localhost console
```

Then run:
```python
import frappe

# Check if DocTypes exist
doctypes = ["CRM Interakt Settings", "CRM WhatsApp Message"]
for dt in doctypes:
    exists = frappe.db.exists("DocType", dt)
    print(f"{dt}: {'✅ EXISTS' if exists else '❌ NOT FOUND'}")

# Try to access settings
settings = frappe.get_single("CRM Interakt Settings")
print(f"\n✅ Settings accessible!")
print(f"Webhook URL: {settings.webhook_url}")
```

---

## 🎯 After Installation:

### 1. Access Settings

**Option A: Search Bar**
- Press `Ctrl + K` (or `Cmd + K` on Mac)
- Type: "CRM Interakt Settings"
- Click to open

**Option B: Direct URL**
```
http://your-site.localhost:8000/app/crm-interakt-settings
```

### 2. Configure Settings

1. ✅ Check **Enabled**
2. 🔑 Enter **API Key** from: https://app.interakt.ai/settings/developer-setting
3. 🌍 Set **Default Country Code**: `+91`
4. 📧 Check **Send Welcome Message on Lead Create** (optional)
5. 💾 Click **Save**

### 3. Test Integration

#### Create a Test Lead:
1. Go to **Leads** → **New**
2. Fill in:
   - First Name: Test
   - Last Name: User
   - Mobile No: Your test number (e.g., 9876543210)
3. Click **Save**

#### Verify Message Sent:
1. Search for "CRM WhatsApp Message"
2. You should see a new message with:
   - Status: Sent
   - Template: seller_registration
   - Phone number: Your test number

#### Check WhatsApp:
- Open WhatsApp on your test number
- You should receive the welcome message with PDF attachment

---

## 🐛 Troubleshooting

### Issue: "No Results found" when searching for settings

**Solution:**
```bash
# Clear cache and restart
bench --site your-site.localhost clear-cache
bench restart

# Verify DocType exists
bench --site your-site.localhost console
>>> import frappe
>>> frappe.db.exists("DocType", "CRM Interakt Settings")
```

### Issue: Migration doesn't create DocTypes

**Solution:**
```bash
# Force reload DocTypes
bench --site your-site.localhost console
```
```python
import frappe
frappe.reload_doctype("CRM Interakt Settings")
frappe.reload_doctype("CRM WhatsApp Message")
frappe.reload_doctype("CRM Telephony Agent")
frappe.db.commit()
```

### Issue: Messages not sending

**Check:**
1. Is Interakt enabled? ✓
2. Is API key correct? ✓
3. Does lead have phone number? ✓
4. Check Error Log for details

---

## 📞 Quick Commands Reference

```bash
# Migrate
bench --site SITE migrate

# Clear cache
bench --site SITE clear-cache

# Restart
bench restart

# Console
bench --site SITE console

# Test integration
bench --site SITE console
>>> from crm.integrations.interakt.test_integration import test_integration
>>> test_integration()

# Create test lead
>>> from crm.integrations.interakt.test_integration import create_test_lead
>>> create_test_lead()
```

---

## ✅ Success Checklist

- [ ] Migration completed without errors
- [ ] Cache cleared
- [ ] Services restarted
- [ ] CRM Interakt Settings accessible
- [ ] API key configured
- [ ] Test lead created
- [ ] Message sent successfully
- [ ] Message received on WhatsApp

---

## 📚 Documentation

- **Setup Guide**: `INTERAKT_SETUP_GUIDE.md`
- **Implementation Details**: `INTERAKT_IMPLEMENTATION_SUMMARY.md`
- **Deployment Checklist**: `INTERAKT_DEPLOYMENT_CHECKLIST.md`
- **Integration README**: `crm/integrations/interakt/README.md`

---

## 🎉 You're All Set!

Once configured, every new lead with a phone number will automatically receive a welcome message via WhatsApp!

**Need help?** Check the Error Log or run the test script to diagnose issues.
