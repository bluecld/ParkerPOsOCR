#!/usr/bin/env python3
"""
Simple script to print a PDF on Mac via SSH
"""
import subprocess
import sys

def print_pdf_manual(po_number):
    """Print PDF with manual SSH (will prompt for password)"""
    
    pdf_path = f"/Users/Shared/ParkerPOsOCR/exports/{po_number}.pdf"
    mac_host = "192.168.0.105"
    ssh_user = "Anthony"
    
    print(f"🖨️ Printing PDF: {pdf_path}")
    print(f"📡 Connecting to {ssh_user}@{mac_host}")
    print("💡 You will be prompted for the SSH password...")
    
    # Simple SSH command that will prompt for password
    ssh_command = f'ssh {ssh_user}@{mac_host} lp "{pdf_path}"'
    
    try:
        # Use subprocess.call to allow interactive password entry
        result = subprocess.call(ssh_command, shell=True)
        
        if result == 0:
            print("✅ PDF sent to printer successfully!")
            return True
        else:
            print(f"❌ Print command failed with exit code: {result}")
            return False
            
    except Exception as e:
        print(f"❌ Print error: {str(e)}")
        return False

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python print_pdf_manual.py <po_number>")
        print("Example: python print_pdf_manual.py 4551240642")
        sys.exit(1)
    
    po_number = sys.argv[1]
    print_pdf_manual(po_number)
