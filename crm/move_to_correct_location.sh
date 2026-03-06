#!/bin/bash

# Script to move CRM files to correct Frappe-Bench location

echo "================================================"
echo "📦 Moving CRM Files to Correct Location"
echo "================================================"
echo ""

# Define paths
CURRENT_DIR="/home/acash/crm"
TARGET_DIR="/home/acash/frappe/frappe-bench/apps/crm"

# Check if current directory exists
if [ ! -d "$CURRENT_DIR" ]; then
    echo "❌ Error: Current directory $CURRENT_DIR not found!"
    exit 1
fi

# Check if target bench exists
if [ ! -d "/home/acash/frappe/frappe-bench" ]; then
    echo "❌ Error: Frappe-Bench not found at /home/acash/frappe/frappe-bench"
    exit 1
fi

echo "📋 Current location: $CURRENT_DIR"
echo "📋 Target location: $TARGET_DIR"
echo ""

# Check if target already exists
if [ -d "$TARGET_DIR" ]; then
    echo "⚠️  Target directory already exists!"
    echo "   This will backup the existing directory and replace it."
    read -p "   Continue? (y/n): " confirm
    if [ "$confirm" != "y" ]; then
        echo "❌ Aborted!"
        exit 1
    fi
    
    # Backup existing directory
    BACKUP_DIR="${TARGET_DIR}_backup_$(date +%Y%m%d_%H%M%S)"
    echo "📦 Backing up existing directory to: $BACKUP_DIR"
    mv "$TARGET_DIR" "$BACKUP_DIR"
fi

# Copy files to target location
echo "📂 Copying files to $TARGET_DIR..."
cp -r "$CURRENT_DIR" "$TARGET_DIR"

if [ $? -eq 0 ]; then
    echo "✅ Files copied successfully!"
else
    echo "❌ Error copying files!"
    exit 1
fi

echo ""
echo "================================================"
echo "✅ Files Moved Successfully!"
echo "================================================"
echo ""
echo "📋 Next Steps:"
echo ""
echo "1. Navigate to frappe-bench:"
echo "   cd /home/acash/frappe/frappe-bench"
echo ""
echo "2. Run migration:"
echo "   bench --site your-site.localhost migrate"
echo ""
echo "3. Clear cache:"
echo "   bench --site your-site.localhost clear-cache"
echo ""
echo "4. Restart:"
echo "   bench restart"
echo ""
echo "5. Access settings:"
echo "   http://your-site.localhost:8000/app/crm-interakt-settings"
echo ""
