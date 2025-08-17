#!/bin/bash
# Setup PDF Auto-Print Monitor to start automatically on Mac boot

echo "🚀 Setting up PDF Monitor Auto-Start Service..."
echo "==============================================="

# Copy LaunchAgent plist to Mac
echo "📤 Copying LaunchAgent configuration..."
if scp com.parkerpos.pdf.autoprint.plist Anthony@192.168.0.105:~/; then
    echo "✅ LaunchAgent file copied"
else
    echo "❌ Failed to copy LaunchAgent file"
    exit 1
fi

# SSH to Mac and install the LaunchAgent
echo "🔧 Installing LaunchAgent on Mac..."
ssh Anthony@192.168.0.105 << 'EOF'
    echo "📁 Setting up LaunchAgent..."
    
    # Create LaunchAgents directory if it doesn't exist
    mkdir -p ~/Library/LaunchAgents
    
    # Move the plist to the correct location
    mv ~/com.parkerpos.pdf.autoprint.plist ~/Library/LaunchAgents/
    
    # Set proper permissions
    chmod 644 ~/Library/LaunchAgents/com.parkerpos.pdf.autoprint.plist
    
    echo "🛑 Stopping any existing monitor..."
    pkill -f pdf_auto_print_monitor 2>/dev/null || true
    
    # Unload any existing LaunchAgent (in case we're updating)
    launchctl unload ~/Library/LaunchAgents/com.parkerpos.pdf.autoprint.plist 2>/dev/null || true
    
    echo "🚀 Loading LaunchAgent..."
    launchctl load ~/Library/LaunchAgents/com.parkerpos.pdf.autoprint.plist
    
    # Start the service
    launchctl start com.parkerpos.pdf.autoprint
    
    sleep 2
    
    echo ""
    echo "✅ LaunchAgent installed successfully!"
    echo "📊 Service status:"
    launchctl list | grep com.parkerpos.pdf.autoprint || echo "Service not found in list"
    
    echo ""
    echo "🔍 Process check:"
    ps aux | grep pdf_auto_print_monitor | grep -v grep || echo "Process not running yet"
    
    echo ""
    echo "📄 Log files:"
    echo "  📋 Output: /Users/Shared/ParkerPOsOCR/pdf_monitor.log"
    echo "  ❌ Errors: /Users/Shared/ParkerPOsOCR/pdf_monitor_error.log"
    
    echo ""
    echo "🎯 The monitor will now:"
    echo "  ✅ Start automatically on Mac boot/login"
    echo "  ✅ Restart automatically if it crashes"
    echo "  ✅ Run continuously in background"
    
    echo ""
    echo "Commands for managing the service:"
    echo "  🛑 Stop:    launchctl unload ~/Library/LaunchAgents/com.parkerpos.pdf.autoprint.plist"
    echo "  🚀 Start:   launchctl load ~/Library/LaunchAgents/com.parkerpos.pdf.autoprint.plist"
    echo "  📊 Status:  launchctl list | grep com.parkerpos.pdf.autoprint"
    
EOF

echo ""
echo "🎉 Auto-start setup complete!"
echo "The PDF monitor will now start automatically when your Mac boots!"
