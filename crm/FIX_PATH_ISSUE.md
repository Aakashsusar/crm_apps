# 🔧 Fix Path Issue - Quick Guide

## 🎯 **The Problem**

Your files are in: `/home/acash/crm/`  
They should be in: `/home/acash/frappe/frappe-bench/apps/crm/`

---

## ✅ **Quick Fix (3 Steps)**

### **Step 1: Check if CRM already exists in correct location**

```bash
ls -la /home/acash/frappe/frappe-bench/apps/crm
```

**If it exists:** Your files might already be there! Skip to Step 3.  
**If it doesn't exist:** Continue to Step 2.

---

### **Step 2: Copy files to correct location**

```bash
# Copy your current files to the correct location
cp -r /home/acash/crm /home/acash/frappe/frappe-bench/apps/

# Verify it worked
ls -la /home/acash/frappe/frappe-bench/apps/crm
```

You should see all your files including:
- `crm/` folder
- `frontend/` folder
- `install_interakt.sh`
- `INTERAKT_README.md`
- etc.

---

### **Step 3: Run Installation from Bench Directory**

```bash
# Navigate to bench directory
cd /home/acash/frappe/frappe-bench

# Run migration
bench --site your-site.localhost migrate

# Clear cache
bench --site your-site.localhost clear-cache

# Restart
bench restart
```

**Replace `your-site.localhost` with your actual site name!**

---

## 🔍 **Find Your Site Name**

If you don't know your site name:

```bash
cd /home/acash/frappe/frappe-bench
ls sites/
```

Look for a folder that's not `assets` or `common_site_config.json`.  
Common names: `site1.local`, `crm.localhost`, `localhost`, etc.

---

## 🧪 **Verify Installation**

After migration, test if it worked:

```bash
cd /home/acash/frappe/frappe-bench
bench --site YOUR-SITE console
```

Then in the console:
```python
import frappe

# Check if DocTypes exist
print(frappe.db.exists("DocType", "CRM Interakt Settings"))
# Should print: CRM Interakt Settings

# Try to access settings
settings = frappe.get_single("CRM Interakt Settings")
print("✅ Settings accessible!")
print(f"Webhook URL: {settings.webhook_url}")
```

Type `exit()` to exit the console.

---

## 🎯 **Access Settings**

Once migration is complete:

1. Open your CRM in browser
2. Press **Ctrl + K**
3. Type: **"CRM Interakt Settings"**
4. Click to open

Or visit directly:
```
http://YOUR-SITE:8000/app/crm-interakt-settings
```

---

## 📋 **Complete Command Sequence**

Copy and paste this (replace YOUR-SITE with your actual site name):

```bash
# 1. Copy files to correct location (if needed)
cp -r /home/acash/crm /home/acash/frappe/frappe-bench/apps/

# 2. Navigate to bench
cd /home/acash/frappe/frappe-bench

# 3. Run migration
bench --site YOUR-SITE migrate

# 4. Clear cache
bench --site YOUR-SITE clear-cache

# 5. Restart
bench restart

# 6. Test
bench --site YOUR-SITE console
```

In console:
```python
import frappe
print(frappe.db.exists("DocType", "CRM Interakt Settings"))
exit()
```

---

## ⚠️ **Common Errors**

### Error: "No module named 'crm'"
**Solution:** Files are not in the correct location. Repeat Step 2.

### Error: "Site not found"
**Solution:** Wrong site name. Check with `ls sites/`

### Error: "Permission denied"
**Solution:** Run with sudo: `sudo bench --site SITE migrate`

---

## 🆘 **Still Not Working?**

Check these:

```bash
# 1. Verify bench location
ls -la /home/acash/frappe/frappe-bench

# 2. Verify CRM in apps
ls -la /home/acash/frappe/frappe-bench/apps/crm

# 3. Verify Interakt files
ls -la /home/acash/frappe/frappe-bench/apps/crm/crm/integrations/interakt

# 4. Check if CRM is installed
cd /home/acash/frappe/frappe-bench
bench list-apps
```

All should show files/folders, not errors.

---

## ✅ **Success Checklist**

- [ ] Files copied to `/home/acash/frappe/frappe-bench/apps/crm`
- [ ] Migration completed without errors
- [ ] Cache cleared
- [ ] Services restarted
- [ ] Can access "CRM Interakt Settings" in UI
- [ ] Console test shows DocType exists

---

**Once all checks pass, you're ready to configure and use Interakt!** 🎉
