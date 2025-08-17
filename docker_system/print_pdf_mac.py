#!/usr/bin/env python3
"""
Script to print PDF files on Mac using lp command
"""
import subprocess
import os

def print_pdf_on_mac(pdf_path, mac_host="192.168.0.105", ssh_user="Anthony", ssh_password="Rynrin12"):
    """Print PDF file on Mac using SSH and lp command"""
    
    # Construct the SSH command to print the PDF
    print_command = f"lp '{pdf_path}'"
    ssh_command = f"sshpass -p '{ssh_password}' ssh {ssh_user}@{mac_host} '{print_command}'"
    
    try:
        result = subprocess.run(ssh_command, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ PDF sent to printer: {pdf_path}")
            print(f"Print job output: {result.stdout.strip()}")
            return True
        else:
            print(f"❌ Print failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Print error: {str(e)}")
        return False

def print_po_pdf(po_number):
    """Print a specific PO's PDF file"""
    pdf_path = f"/Users/Shared/ParkerPOsOCR/exports/{po_number}.pdf"
    return print_pdf_on_mac(pdf_path)

if __name__ == "__main__":
    # Test with a PO number
    test_po = "4551240642"
    print_po_pdf(test_po)
