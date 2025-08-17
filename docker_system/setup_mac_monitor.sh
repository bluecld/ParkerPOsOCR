#!/bin/bash
# Setup script to install and run the PDF auto-print monitor on Mac

echo "🎯 Setting up PDF Auto-Print Monitor on Mac..."
echo "================================================="

# Copy the monitor script to Mac
echo "📤 Copying monitor script to Mac..."
scp pdf_auto_print_monitor.py Anthony@192.168.0.105:/Users/Shared/ParkerPOsOCR/

# SSH to Mac and set up the environment
echo "🔧 Setting up Python environment on Mac..."
ssh Anthony@192.168.0.105 << 'EOF'
    # Install watchdog library if not present
    echo "📦 Installing required Python packages..."
    python3 -m pip install --user watchdog
    
    # Make the script executable
    chmod +x /Users/Shared/ParkerPOsOCR/pdf_auto_print_monitor.py
    
    # Create a simple start script
    cat > /Users/Shared/ParkerPOsOCR/start_monitor.sh << 'SCRIPT_EOF'
#!/bin/bash
echo "Starting PDF Auto-Print Monitor..."
cd /Users/Shared/ParkerPOsOCR
python3 pdf_auto_print_monitor.py
SCRIPT_EOF
    
    chmod +x /Users/Shared/ParkerPOsOCR/start_monitor.sh
    
    echo "✅ Setup complete!"
    echo "📍 Monitor script location: /Users/Shared/ParkerPOsOCR/pdf_auto_print_monitor.py"
    echo "🚀 To start monitoring, run: ./start_monitor.sh"
    
EOF

echo "🎉 Setup complete! SSH to your Mac and run the monitor."
