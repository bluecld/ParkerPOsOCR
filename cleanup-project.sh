#!/bin/sh
# Parker PO OCR Project Cleanup Script
# Run this to clean up temporary files and organize documentation

echo "🧹 Starting ParkerPOsOCR cleanup..."

# Create organized directories
mkdir -p docs/legacy docs/guides docs/troubleshooting

echo "📝 Organizing documentation..."
# Move legacy documentation to organized structure
mv DASHBOARD_*FIX.md NOTIFICATION_*FIX.md docs/troubleshooting/ 2>/dev/null
mv *GUIDE.md *SETUP.md docs/guides/ 2>/dev/null
mv ISSUES_RESOLVED* IMPLEMENTATION* docs/legacy/ 2>/dev/null

echo "🗑️ Cleaning temporary files..."
# Clean up log files older than 7 days
find . -name "*.log" -mtime +7 -delete 2>/dev/null

# Move test files to appropriate locations
mv Sample.pdf Archive/ 2>/dev/null
mv cookies.txt logs/ 2>/dev/null

# Remove empty directories
rmdir Errors/ Scans/ 2>/dev/null

echo "🎯 Cleanup suggestions:"
echo "- Review docs/legacy/ for files that can be deleted"
echo "- Consider archiving old PO data outside project folder"
echo "- Set up log rotation for dashboard logs"

echo "✅ Cleanup complete!"
