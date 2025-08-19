#!/bin/sh

# Script to restart LaunchAgent on Mac via SSH key authentication
echo "Attempting to restart LaunchAgent via SSH..."

# Try with key authentication and strict timeout
ssh -o ConnectTimeout=5 -o BatchMode=yes -o StrictHostKeyChecking=no -i ~/.ssh/parkerpos_ed25519 parker@192.168.0.105 << 'ENDSSH'
    launchctl unload ~/Library/LaunchAgents/com.parkerpos.pdf.autoprint.plist 2>/dev/null
    launchctl load ~/Library/LaunchAgents/com.parkerpos.pdf.autoprint.plist
    if launchctl list com.parkerpos.pdf.autoprint >/dev/null 2>&1; then
        echo "LaunchAgent successfully restarted"
    else
        echo "LaunchAgent restart failed"
    fi
ENDSSH

echo "SSH command completed"
