# Ipshopy CRM (Frappe App)

Custom CRM application built on Frappe Framework for Ipshopy, featuring:
- **Department Hierarchy**: Custom lead distribution based on departments and sales teams
- **Telephony Integration**: Tata Smartflo & Twilio integration for click-to-call and call logging
- **WhatsApp Integration**: Interakt-based WhatsApp templates and messaging
- **Facebook Lead Ads**: Real-time webhook integration for Facebook leads

## 🛠 Prerequisites (Ubuntu 22.04)

Ensure your server meets these requirements:
- **OS**: Ubuntu 22.04 LTS
- **Frappe Bench**: v5.x
- **Python**: v3.10+
- **Node.js**: v18+
- **MariaDB**: v10.6+
- **Redis**: v6+

## 🚀 Installation Guide

### 1. Install Frappe Bench (If not already installed)
If you have a fresh server, first install Frappe Bench:

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install dependencies
sudo apt install -y git python3-dev python3-pip redis-server mariadb-server libmariadb-dev-compat libmariadb-dev nodejs npm xvfb libfontconfig wkhtmltopdf

# Install Frappe Bench
pip3 install frappe-bench

# Initialize Bench (replace 'frappe-bench' with your desired directory name)
bench init frappe-bench --frappe-branch version-15
cd frappe-bench
```

### 2. Get the App

Pull the CRM app into your bench:

```bash
# Get the app from GitHub
bench get-app https://github.com/AchintyaCh/ipshopy-crm.git

# Verify app is present
ls -la apps/crm
```

### 3. Install App on Site

Install the app on your specific site (replace `site1.local` with your site name):

```bash
# Install app
bench --site site1.local install-app crm

# Verify installation
bench --site site1.local list-apps
```

### 4. Build & Migrate (Critical Step)

Run migration to create all custom doctypes and apply patches:

```bash
# Build frontend assets
bench build --app crm

# Run database migration (Applies all patches and schema changes)
bench --site site1.local migrate
```

*Note: If `bench migrate` fails, check the troubleshooting section below.*

### 5. Restart Services

Apply changes by restarting the bench workers:

```bash
# For production (Supervisor/Nginx)
sudo supervisorctl restart all

# For development
bench restart
```

---

## 🔧 Configuration & Setup

### 1. Configure Telephony
1. Go to **Telephony Settings** in CRM.
2. Enter your Tata Smartflo / Twilio API credentials.
3. Map agents in **Smartflo Agent Mapping** doctype.

### 2. Configure WhatsApp (Interakt)
1. Go to **CRM Interakt Settings**.
2. Enable the integration and add your API Key.
3. Set up the webhook URL in your Interakt dashboard.

### 3. Configure Facebook Lead Ads
1. Go to **FCRM Settings** -> **Facebook Integration**.
2. Generate a Verify Token and save it.
3. Copy the Webhook URL to Meta Developer Console.

---

## ❓ Troubleshooting & Error Handling

### 1. `ModuleNotFoundError` during migration
If you see missing Python module errors:

```bash
# Install requirements locally
./env/bin/pip install -r apps/crm/requirements.txt

# Reload bench
bench restart
```

### 2. Frontend Assets Not Loading
If CRM dashboard or pages look broken:

```bash
# Force rebuild assets
bench build --app crm --force

# Clear cache
bench --site site1.local clear-cache
```

### 3. "Doctype Not Found" Errors
If updates or patches fail due to missing doctypes:

```bash
# Reload doctypes manually
bench --site site1.local reload-doctype "CRM Lead" "CRM Deal" "Contact"

# Run migrate again
bench --site site1.local migrate
```

### 4. Permission Errors
If you face permission issues:

```bash
# Reset file permissions
sudo chown -R $USER:$USER .
```
