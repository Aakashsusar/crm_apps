# 📂 Correct File Structure for Frappe CRM

## 🎯 **Understanding the Structure**

Frappe uses a specific directory structure. Here's how it should look:

```
/home/acash/
│
└── frappe/
    └── frappe-bench/                    ← Main Bench Directory
        ├── apps/                        ← All Frappe apps go here
        │   ├── frappe/                  ← Frappe Framework
        │   ├── crm/                     ← CRM App (YOUR CODE GOES HERE)
        │   │   ├── crm/                 ← Python backend
        │   │   │   ├── api/
        │   │   │   ├── fcrm/
        │   │   │   │   └── doctype/
        │   │   │   │       ├── crm_interakt_settings/
        │   │   │   │       ├── crm_whatsapp_message/
        │   │   │   │       └── ...
        │   │   │   ├── integrations/
        │   │   │   │   └── interakt/
        │   │   │   │       ├── __init__.py
        │   │   │   │       ├── interakt_handler.py
        │   │   │   │       ├── api.py
        │   │   │   │       ├── utils.py
        │   │   │   │       └── webhooks.py
        │   │   │   └── hooks.py
        │   │   ├── frontend/            ← Vue.js frontend
        │   │   ├── install_interakt.sh  ← Installation scripts
        │   │   ├── install_interakt.ps1
        │   │   ├── INTERAKT_README.md   ← Documentation
        │   │   └── ...
        │   └── erpnext/                 ← ERPNext (if installed)
        │
        ├── sites/                       ← Site directories
        │   ├── your-site.localhost/
        │   └── common_site_config.json
        │
        ├── config/                      ← Configuration files
        ├── logs/                        ← Log files
        └── env/                         ← Python virtual environment
```

---

## ⚠️ **Your Current Problem**

You have files in:
```
/home/acash/crm/          ← WRONG LOCATION!
```

They should be in:
```
/home/acash/frappe/frappe-bench/apps/crm/    ← CORRECT LOCATION!
```

---

## ✅ **Solution: Move Files**

### **Option 1: Automated Script**

Run the move script:
```bash
cd /home/acash/crm
bash move_to_correct_location.sh
```

### **Option 2: Manual Move**

```bash
# Backup existing CRM app (if any)
cd /home/acash/frappe/frappe-bench/apps
mv crm crm_backup_$(date +%Y%m%d)

# Copy your files to correct location
cp -r /home/acash/crm /home/acash/frappe/frappe-bench/apps/crm

# Verify
ls -la /home/acash/frappe/frappe-bench/apps/crm
```

### **Option 3: Use Symbolic Link (Advanced)**

If you want to keep files in current location but make them accessible:
```bash
cd /home/acash/frappe/frappe-bench/apps
ln -s /home/acash/crm crm
```

---

## 🚀 **After Moving Files**

### **1. Navigate to Bench Directory**
```bash
cd /home/acash/frappe/frappe-bench
```

### **2. Verify CRM App is Recognized**
```bash
bench --site your-site.localhost list-apps
```

You should see `crm` in the list.

### **3. Run Migration**
```bash
bench --site your-site.localhost migrate
```

### **4. Clear Cache**
```bash
bench --site your-site.localhost clear-cache
```

### **5. Restart**
```bash
bench restart
```

---

## 📍 **Important Paths Reference**

| What | Path |
|------|------|
| **Bench Root** | `/home/acash/frappe/frappe-bench` |
| **CRM App** | `/home/acash/frappe/frappe-bench/apps/crm` |
| **CRM Backend** | `/home/acash/frappe/frappe-bench/apps/crm/crm` |
| **CRM Frontend** | `/home/acash/frappe/frappe-bench/apps/crm/frontend` |
| **Interakt Integration** | `/home/acash/frappe/frappe-bench/apps/crm/crm/integrations/interakt` |
| **DocTypes** | `/home/acash/frappe/frappe-bench/apps/crm/crm/fcrm/doctype` |
| **Sites** | `/home/acash/frappe/frappe-bench/sites` |

---

## 🧪 **Verify Correct Structure**

Run this to check:
```bash
cd /home/acash/frappe/frappe-bench

# Check if CRM app exists
ls -la apps/crm

# Check if Interakt integration exists
ls -la apps/crm/crm/integrations/interakt

# Check if DocTypes exist
ls -la apps/crm/crm/fcrm/doctype/crm_interakt_settings
ls -la apps/crm/crm/fcrm/doctype/crm_whatsapp_message
```

All commands should show files, not "No such file or directory".

---

## 🎯 **Working Directory for Commands**

Always run bench commands from the bench root:

```bash
# CORRECT ✅
cd /home/acash/frappe/frappe-bench
bench --site your-site.localhost migrate

# WRONG ❌
cd /home/acash/crm
bench --site your-site.localhost migrate  # This won't work!
```

---

## 📝 **Quick Reference**

### **Navigate to Bench:**
```bash
cd ~/frappe/frappe-bench
```

### **Navigate to CRM App:**
```bash
cd ~/frappe/frappe-bench/apps/crm
```

### **Navigate to Interakt Integration:**
```bash
cd ~/frappe/frappe-bench/apps/crm/crm/integrations/interakt
```

### **Run Bench Commands:**
```bash
cd ~/frappe/frappe-bench
bench [command]
```

---

## ✅ **Checklist After Moving**

- [ ] Files moved to `/home/acash/frappe/frappe-bench/apps/crm`
- [ ] Can navigate to bench: `cd ~/frappe/frappe-bench`
- [ ] CRM app listed: `bench list-apps` shows `crm`
- [ ] Migration runs: `bench --site SITE migrate`
- [ ] No errors in migration
- [ ] Settings accessible: Search "CRM Interakt Settings"

---

## 🆘 **Still Having Issues?**

If you're still having path issues:

1. **Check current directory:**
   ```bash
   pwd
   ```

2. **Check if bench exists:**
   ```bash
   ls -la ~/frappe/frappe-bench
   ```

3. **Check if CRM is in apps:**
   ```bash
   ls -la ~/frappe/frappe-bench/apps/crm
   ```

4. **Verify bench can see CRM:**
   ```bash
   cd ~/frappe/frappe-bench
   bench list-apps
   ```

---

**Once files are in the correct location, run the installation script from the bench directory!** 🚀
