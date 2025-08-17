#!/bin/bash
# Install updated PDF monitor with printed folder functionality

echo "🔧 Installing Updated PDF Auto-Print Monitor..."
echo "================================================="

# Copy the updated monitor script
echo "📤 Copying updated monitor script..."
if scp pdf_auto_print_monitor.py Anthony@192.168.0.105:/Users/Shared/ParkerPOsOCR/; then
    echo "✅ Script copied successfully"
else
    echo "❌ Failed to copy script"
    exit 1
fi

# SSH to Mac and set up
echo "🔧 Setting up on Mac..."
ssh Anthony@192.168.0.105 << 'EOF'
    cd /Users/Shared/ParkerPOsOCR
    
    # Make executable
    chmod +x pdf_auto_print_monitor.py
    
    # Create printed directory
    mkdir -p exports/printed
    echo "📂 Created printed directory: exports/printed/"
    
    # Update the background startup script
    cat > start_pdf_monitor.sh << 'SCRIPT_EOF'
#!/bin/bash
echo "🚀 Starting PDF Auto-Print Monitor (with printed folder) in background..."
cd /Users/Shared/ParkerPOsOCR

# Kill any existing monitor
pkill -f pdf_auto_print_monitor 2>/dev/null

# Start new monitor
nohup python3 pdf_auto_print_monitor.py --auto > pdf_monitor.log 2>&1 &
MONITOR_PID=$!

echo "✅ Monitor started! PID: $MONITOR_PID"
echo "📁 Watching: /Users/Shared/ParkerPOsOCR/exports/"
echo "📂 Printed files moved to: exports/printed/"
echo "📄 Log file: pdf_monitor.log"
echo ""
echo "Commands:"
echo "  📊 Check status: ps aux | grep pdf_auto_print_monitor"
echo "  📄 View log: tail -f pdf_monitor.log"
echo "  🛑 Stop monitor: pkill -f pdf_auto_print_monitor"
SCRIPT_EOF
    
    chmod +x start_pdf_monitor.sh
    
    echo ""
    echo "✅ Installation complete!"
    echo "📂 Folder structure:"
    echo "   exports/          <- New PDFs appear here"
    echo "   exports/printed/  <- Printed PDFs moved here"
    echo ""
    echo "🚀 To start: ./start_pdf_monitor.sh"
    
EOF

echo "🎉 Installation complete!"
