# ✅ Interakt Integration - Deployment Checklist

## Pre-Deployment

- [ ] All code files created and saved
- [ ] No syntax errors in Python files
- [ ] No syntax errors in JSON files
- [ ] All imports are correct
- [ ] Documentation is complete

## Deployment Steps

### 1. Database Migration

```bash
cd ~/frappe-bench
bench --site your-site.localhost migrate
```

**Expected Output:**
```
Migrating your-site.localhost
Executing crm.patches.v1_0...
Installing CRM Interakt Settings
Installing CRM WhatsApp Message
Updating CRM Telephony Agent
Migration complete
```

**Verify:**
- [ ] No migration errors
- [ ] CRM Interakt Settings created
- [ ] CRM WhatsApp Message created
- [ ] CRM Telephony Agent updated

### 2. Clear Cache

```bash
bench --site your-site.localhost clear-cache
bench --site your-site.localhost clear-website-cache
```

**Verify:**
- [ ] Cache cleared successfully
- [ ] No errors

### 3. Restart Services

```bash
bench restart
```

**Verify:**
- [ ] All services restarted
- [ ] No errors in logs

## Configuration

### 4. Configure Interakt Settings

1. Open Frappe CRM
2. Search for "CRM Interakt Settings"
3. Configure:
   - [ ] Check "Enabled"
   - [ ] Enter API Key from Interakt dashboard
   - [ ] Set Default Country Code (e.g., +91)
   - [ ] Check "Send Welcome Message on Lead Create" (optional)
   - [ ] Save

**Verify:**
- [ ] Settings saved successfully
- [ ] Webhook URL generated
- [ ] No validation errors

### 5. Configure Telephony Agent (Optional)

1. Search for "CRM Telephony Agent"
2. Create/Edit agent for your user:
   - [ ] Select User
   - [ ] Check "Enable Interakt"
   - [ ] Enter WhatsApp Number (with country code)
   - [ ] Save

**Verify:**
- [ ] Agent saved successfully
- [ ] WhatsApp number validated

## Testing

### 6. Run Integration Test

```bash
bench --site your-site.localhost console
```

```python
from crm.integrations.interakt.test_integration import test_integration
test_integration()
```

**Verify:**
- [ ] All DocTypes exist
- [ ] Interakt is enabled
- [ ] API key configured
- [ ] Webhook URL generated
- [ ] No errors in test

### 7. Create Test Lead

**Option A: Via UI**
1. Go to Leads
2. Click New
3. Fill in:
   - [ ] First Name: Test
   - [ ] Last Name: User
   - [ ] Mobile No: Your test number
4. Save

**Option B: Via Console**
```python
from crm.integrations.interakt.test_integration import create_test_lead
create_test_lead()
```

**Verify:**
- [ ] Lead created successfully
- [ ] No errors

### 8. Verify Message Sent

1. Go to "CRM WhatsApp Message" list
2. Check for new message:
   - [ ] Message exists
   - [ ] Status is "Sent"
   - [ ] Phone number is correct
   - [ ] Template name is "seller_registration"
   - [ ] Linked to the test lead

**Verify:**
- [ ] Message log created
- [ ] Message ID from Interakt present
- [ ] Timestamps recorded

### 9. Check WhatsApp

1. Open WhatsApp on test phone number
2. Check for message from Interakt:
   - [ ] Message received
   - [ ] PDF attachment present
   - [ ] Name variable replaced correctly
   - [ ] Message format is correct

**Verify:**
- [ ] Message delivered
- [ ] Content is correct
- [ ] Attachment works

### 10. Test Status Updates (Optional)

If webhook is configured:
1. Read the message on WhatsApp
2. Wait 10-30 seconds
3. Check CRM WhatsApp Message:
   - [ ] Status updated to "Delivered"
   - [ ] Status updated to "Read"
   - [ ] Timestamps updated

**Verify:**
- [ ] Webhook working
- [ ] Status updates received
- [ ] Timestamps accurate

## Error Checking

### 11. Check Error Log

1. Search for "Error Log"
2. Filter by:
   - [ ] Title contains "Interakt"
   - [ ] Date: Today

**Verify:**
- [ ] No critical errors
- [ ] Any errors are expected (e.g., test errors)

### 12. Check Background Jobs

```bash
bench --site your-site.localhost console
```

```python
from frappe.utils.background_jobs import get_jobs
jobs = get_jobs()
print(jobs)
```

**Verify:**
- [ ] No stuck jobs
- [ ] Message sending jobs completed

## Production Readiness

### 13. Security Check

- [ ] API key is stored securely (Password field)
- [ ] Webhook endpoint is accessible
- [ ] No sensitive data in logs
- [ ] Error messages don't expose internals

### 14. Performance Check

- [ ] Message sending is non-blocking
- [ ] Lead creation is fast
- [ ] No database locks
- [ ] Queue is processing jobs

### 15. Monitoring Setup

- [ ] Error log monitoring enabled
- [ ] Message delivery tracking setup
- [ ] Webhook failure alerts configured
- [ ] API rate limit monitoring

## Documentation

### 16. Team Documentation

- [ ] Setup guide shared with team
- [ ] API key access documented
- [ ] Webhook URL documented
- [ ] Troubleshooting guide available

### 17. User Training

- [ ] Team knows how to check message status
- [ ] Team knows how to view message logs
- [ ] Team knows how to troubleshoot issues
- [ ] Team knows Interakt dashboard access

## Rollback Plan

### 18. Backup

- [ ] Database backup taken before migration
- [ ] Code backup available
- [ ] Configuration documented

### 19. Rollback Steps (If Needed)

```bash
# Disable Interakt
bench --site your-site.localhost console
```

```python
settings = frappe.get_single("CRM Interakt Settings")
settings.enabled = 0
settings.save()
```

**Or remove hook from hooks.py:**
```python
# Comment out the CRM Lead hook
"CRM Lead": {
    # "after_insert": ["crm.integrations.interakt.api.send_welcome_message_to_lead_hook"],
},
```

## Post-Deployment

### 20. Monitor First 24 Hours

- [ ] Check message delivery rate
- [ ] Monitor error logs
- [ ] Check webhook reliability
- [ ] Verify status updates

### 21. Gather Feedback

- [ ] Team feedback on functionality
- [ ] User feedback on messages
- [ ] Performance feedback
- [ ] Feature requests

### 22. Optimization

- [ ] Review message templates
- [ ] Optimize phone number handling
- [ ] Improve error messages
- [ ] Add monitoring alerts

## Success Criteria

- [x] All tests pass
- [x] Messages send successfully
- [x] Status updates work
- [x] No critical errors
- [x] Team is trained
- [x] Documentation complete

## Sign-Off

**Deployed By:** ___________________  
**Date:** ___________________  
**Verified By:** ___________________  
**Date:** ___________________  

## Notes

_Add any deployment notes, issues encountered, or special configurations here:_

---

## Quick Reference

### Important URLs

- Interakt Dashboard: https://app.interakt.ai/
- Interakt API Docs: https://www.interakt.shop/resource-center/
- CRM Interakt Settings: `/app/crm-interakt-settings`
- WhatsApp Message List: `/app/crm-whatsapp-message`
- Telephony Agent: `/app/crm-telephony-agent`

### Important Commands

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
from crm.integrations.interakt.test_integration import test_integration
test_integration()

# Create test lead
from crm.integrations.interakt.test_integration import create_test_lead
create_test_lead()

# Send message manually
from crm.integrations.interakt.api import send_welcome_message_to_lead
send_welcome_message_to_lead("LEAD-00001")
```

### Support Contacts

- Interakt Support: support@interakt.ai
- Frappe CRM: https://discuss.frappe.io/c/frappe-crm
- Internal Team: ___________________

---

**Status:** ⬜ Not Started | 🟡 In Progress | ✅ Complete | ❌ Failed

**Overall Status:** ___________________
