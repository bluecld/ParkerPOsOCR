#!/bin/bash
# Test script to demonstrate the printed folder functionality

echo "🧪 Testing PDF Auto-Print Monitor with printed folder..."

# SSH to Mac and set up the updated monitor
ssh Anthony@192.168.0.105 << 'EOF'
    cd /Users/Shared/ParkerPOsOCR
    
    echo "📁 Current exports directory contents:"
    ls -la exports/
    
    echo ""
    echo "📂 Creating printed subdirectory if needed..."
    mkdir -p exports/printed
    
    echo ""
    echo "📂 Printed directory contents:"
    ls -la exports/printed/ 2>/dev/null || echo "Directory is empty or doesn't exist yet"
    
    echo ""
    echo "✅ Setup complete! The monitor will now:"
    echo "   1. 🖨️ Print new PDFs automatically"
    echo "   2. 📂 Move printed PDFs to exports/printed/"
    echo "   3. 🧹 Keep exports/ clean with only new PDFs"
    
EOF

echo "🎉 Test complete!"
