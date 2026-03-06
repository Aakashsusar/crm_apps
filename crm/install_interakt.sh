#!/bin/bash

# Interakt Integration Installation Script
# This script installs and configures the Interakt WhatsApp integration for Frappe CRM

echo "================================================"
echo "🚀 Interakt Integration Installation Script"
echo "================================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get the site name
read -p "Enter your site name (e.g., crm.localhost): " SITE_NAME

if [ -z "$SITE_NAME" ]; then
    echo -e "${RED}❌ Site name is required!${NC}"
    exit 1
fi

echo ""
echo -e "${YELLOW}�s Installation Steps:${NC}"
echo "1. Run database migration"
echo "2. Clear cache"
echo "3. Restart services"
echo "4. Verify installation"
echo ""

# Step 1: Run Migration
echo -e "${YELLOW}Step 1: Running database migration...${NC}"
bench --site $SITE_NAME migrate

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Migration completed successfully${NC}"
else
    echo -e "${RED}❌ Migration failed!${NC}"
    exit 1
fi

echo ""

# Step 2: Clear Cache
echo -e "${YELLOW}Step 2: Clearing cache...${NC}"
bench --site $SITE_NAME clear-cache
bench --site $SITE_NAME clear-website-cache

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Cache cleared successfully${NC}"
else
    echo -e "${RED}❌ Cache clearing failed!${NC}"
    exit 1
fi

echo ""

# Step 3: Restart Services
echo -e "${YELLOW}Step 3: Restarting services...${NC}"
bench restart

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Services restarted successfully${NC}"
else
    echo -e "${RED}❌ Service restart failed!${NC}"
    exit 1
fi

echo ""

# Step 4: Verify Installation
echo -e "${YELLOW}Step 4: Verifying installation...${NC}"

bench --site $SITE_NAME console << 'PYTHON_SCRIPT'
import frappe

print("\n🔍 Checking DocTypes...")

doctypes = [
    "CRM Interakt Settings",
    "CRM WhatsApp Message",
    "CRM Telephony Agent",
]

all_exist = True
for dt in doctypes:
    exists = frappe.db.exists("DocType", dt)
    status = "✅" if exists else "❌"
    print(f"   {status} {dt}")
    if not exists:
        all_exist = False

if all_exist:
    print("\n✅ All DocTypes installed successfully!")
    
    # Check if settings can be accessed
    try:
        settings = frappe.get_single("CRM Interakt Settings")
        print(f"\n📋 CRM Interakt Settings:")
        print(f"   - Enabled: {settings.enabled}")
        print(f"   - Default Country Code: {settings.default_country_code}")
        print(f"   - Auto-send Welcome: {settings.send_welcome_on_lead_create}")
        if settings.webhook_url:
            print(f"   - Webhook URL: {settings.webhook_url}")
    except Exception as e:
        print(f"\n⚠️  Could not access settings: {e}")
else:
    print("\n❌ Some DocTypes are missing!")
    exit(1)

print("\n" + "="*60)
print("✅ INSTALLATION COMPLETE!")
print("="*60)

PYTHON_SCRIPT

echo ""
echo -e "${GREEN}================================================${NC}"
echo -e "${GREEN}✅ Interakt Integration Installed Successfully!${NC}"
echo -e "${GREEN}================================================${NC}"
echo ""
echo -e "${YELLOW}📋 Next Steps:${NC}"
echo ""
echo "1. Access CRM Interakt Settings:"
echo "   - Press Ctrl+K and search for 'CRM Interakt Settings'"
echo "   - Or visit: http://$SITE_NAME:8000/app/crm-interakt-settings"
echo ""
echo "2. Configure the settings:"
echo "   ✓ Enable Interakt"
echo "   ✓ Add your API Key from https://app.interakt.ai/settings/developer-setting"
echo "   ✓ Set Default Country Code (e.g., +91)"
echo "   ✓ Enable 'Send Welcome Message on Lead Create' (optional)"
echo ""
echo "3. Test the integration:"
echo "   - Create a new lead with a phone number"
echo "   - Check 'CRM WhatsApp Message' list for the sent message"
echo ""
echo -e "${YELLOW}📚 Documentation:${NC}"
echo "   - Setup Guide: INTERAKT_SETUP_GUIDE.md"
echo "   - Implementation Summary: INTERAKT_IMPLEMENTATION_SUMMARY.md"
echo "   - Deployment Checklist: INTERAKT_DEPLOYMENT_CHECKLIST.md"
echo ""
echo -e "${YELLOW}🧪 Run Test:${NC}"
echo "   bench --site $SITE_NAME console"
echo "   >>> from crm.integrations.interakt.test_integration import test_integration"
echo "   >>> test_integration()"
echo ""
echo -e "${GREEN}Happy messaging! 🎉${NC}"
echo ""
