# Interakt Integration Installation Script (PowerShell)
# This script installs and configures the Interakt WhatsApp integration for Frappe CRM

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "🚀 Interakt Integration Installation Script" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

# Get the site name
$SITE_NAME = Read-Host "Enter your site name (e.g., crm.localhost)"

if ([string]::IsNullOrWhiteSpace($SITE_NAME)) {
    Write-Host "❌ Site name is required!" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "📋 Installation Steps:" -ForegroundColor Yellow
Write-Host "1. Run database migration"
Write-Host "2. Clear cache"
Write-Host "3. Restart services"
Write-Host "4. Verify installation"
Write-Host ""

# Step 1: Run Migration
Write-Host "Step 1: Running database migration..." -ForegroundColor Yellow
bench --site $SITE_NAME migrate

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Migration completed successfully" -ForegroundColor Green
} else {
    Write-Host "❌ Migration failed!" -ForegroundColor Red
    exit 1
}

Write-Host ""

# Step 2: Clear Cache
Write-Host "Step 2: Clearing cache..." -ForegroundColor Yellow
bench --site $SITE_NAME clear-cache
bench --site $SITE_NAME clear-website-cache

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Cache cleared successfully" -ForegroundColor Green
} else {
    Write-Host "❌ Cache clearing failed!" -ForegroundColor Red
    exit 1
}

Write-Host ""

# Step 3: Restart Services
Write-Host "Step 3: Restarting services..." -ForegroundColor Yellow
bench restart

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Services restarted successfully" -ForegroundColor Green
} else {
    Write-Host "❌ Service restart failed!" -ForegroundColor Red
    exit 1
}

Write-Host ""

# Step 4: Verify Installation
Write-Host "Step 4: Verifying installation..." -ForegroundColor Yellow

$pythonScript = @"
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

print("\n" + "="*60)
print("✅ INSTALLATION COMPLETE!")
print("="*60)
"@

$pythonScript | bench --site $SITE_NAME console

Write-Host ""
Write-Host "================================================" -ForegroundColor Green
Write-Host "✅ Interakt Integration Installed Successfully!" -ForegroundColor Green
Write-Host "================================================" -ForegroundColor Green
Write-Host ""
Write-Host "📋 Next Steps:" -ForegroundColor Yellow
Write-Host ""
Write-Host "1. Access CRM Interakt Settings:"
Write-Host "   - Press Ctrl+K and search for 'CRM Interakt Settings'"
Write-Host "   - Or visit: http://$SITE_NAME:8000/app/crm-interakt-settings"
Write-Host ""
Write-Host "2. Configure the settings:"
Write-Host "   ✓ Enable Interakt"
Write-Host "   ✓ Add your API Key from https://app.interakt.ai/settings/developer-setting"
Write-Host "   ✓ Set Default Country Code (e.g., +91)"
Write-Host "   ✓ Enable 'Send Welcome Message on Lead Create' (optional)"
Write-Host ""
Write-Host "3. Test the integration:"
Write-Host "   - Create a new lead with a phone number"
Write-Host "   - Check 'CRM WhatsApp Message' list for the sent message"
Write-Host ""
Write-Host "📚 Documentation:" -ForegroundColor Yellow
Write-Host "   - Setup Guide: INTERAKT_SETUP_GUIDE.md"
Write-Host "   - Implementation Summary: INTERAKT_IMPLEMENTATION_SUMMARY.md"
Write-Host "   - Deployment Checklist: INTERAKT_DEPLOYMENT_CHECKLIST.md"
Write-Host ""
Write-Host "🧪 Run Test:" -ForegroundColor Yellow
Write-Host "   bench --site $SITE_NAME console"
Write-Host "   >>> from crm.integrations.interakt.test_integration import test_integration"
Write-Host "   >>> test_integration()"
Write-Host ""
Write-Host "Happy messaging! 🎉" -ForegroundColor Green
Write-Host ""
