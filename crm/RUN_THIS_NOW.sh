#!/bin/bash

# WhatsApp Integration - Quick Test Script
# Run this from your WSL terminal

echo "=================================================="
echo "🚀 WhatsApp Integration - Quick Test"
echo "=================================================="
echo ""

# Navigate to bench directory
echo "📁 Navigating to bench directory..."
cd ~/frappe/frappe-bench || exit

echo ""
echo "🔄 Step 1: Restarting bench..."
bench restart

echo ""
echo "✨ Step 2: Clearing cache..."
bench --site ipshopy.localhost clear-cache

echo ""
echo "=================================================="
echo "✅ Setup Complete!"
echo "=================================================="
echo ""
echo "📋 Next Steps:"
echo ""
echo "1️⃣  Test Backend (Run in console):"
echo "    bench --site ipshopy.localhost console"
echo "    Then: exec(open('test_text_message_backend.py').read())"
echo ""
echo "2️⃣  Test Frontend (Open in browser):"
echo "    http://ipshopy.localhost:8000/crm/leads"
echo "    • Click any lead with phone number"
echo "    • Click 'WhatsApp' tab"
echo "    • Type a message and press Enter"
echo "    • Check your WhatsApp! 📱"
echo ""
echo "=================================================="
echo "📚 Documentation:"
echo "=================================================="
echo ""
echo "• WHATSAPP_QUICK_START.md - Quick reference"
echo "• TEST_WHATSAPP_INTEGRATION.md - Detailed testing"
echo "• WHATSAPP_IMPLEMENTATION_COMPLETE.md - Full docs"
echo ""
echo "=================================================="
echo "🎉 Ready to test!"
echo "=================================================="
