#!/bin/bash
echo "🔍 Checking PDF Auto-Print Monitor Results..."
echo "=" * 50

ssh Anthony@192.168.0.105 << 'EOF'
    echo "📁 Current exports directory:"
    ls -la /Users/Shared/ParkerPOsOCR/exports/
    
    echo ""
    echo "📂 Printed directory contents:"
    ls -la /Users/Shared/ParkerPOsOCR/exports/printed/
    
    echo ""
    echo "🔍 Monitor process status:"
    ps aux | grep pdf_auto_print_monitor | grep -v grep || echo "Monitor not running"
    
    echo ""
    echo "📄 Recent print log entries:"
    tail -5 /Users/Shared/ParkerPOsOCR/print_log.txt 2>/dev/null || echo "No print log found yet"
    
EOF
