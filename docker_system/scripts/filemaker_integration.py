"""
FileMaker Data API Integration for PO Processing
Phase 1b - To be used after container testing is complete
"""

import json
import os
from datetime import datetime
import requests
import urllib3

# Suppress SSL certificate warnings for self-signed certificates
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class FileMakerIntegration:
    def __init__(self):
        self.server = os.getenv('FILEMAKER_SERVER', 'https://192.168.0.105:443')
        self.database = os.getenv('FILEMAKER_DATABASE', 'PreInventory')
        self.layout = os.getenv('FILEMAKER_LAYOUT', 'PreInventory')  # Changed from Time Clock to PreInventory
        self.username = os.getenv('FILEMAKER_USERNAME', 'JSON')
        self.password = os.getenv('FILEMAKER_PASSWORD', 'Windu63Purple!')
        self.token = None
        
    def authenticate(self):
        """Authenticate with FileMaker Data API"""
        url = f"{self.server}/fmi/data/v1/databases/{self.database}/sessions"
        
        # FileMaker Data API requires Basic Authentication in the header
        import base64
        credentials = f"{self.username}:{self.password}"
        encoded_credentials = base64.b64encode(credentials.encode('utf-8')).decode('utf-8')
        
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Basic {encoded_credentials}'
        }
        
        try:
            # For sessions endpoint, we send an empty JSON body
            response = requests.post(url, json={}, headers=headers, verify=False)
            if response.status_code == 200:
                self.token = response.json()['response']['token']
                print("✅ FileMaker authentication successful")
                return True
            else:
                print(f"❌ FileMaker authentication failed: {response.status_code}")
                print(f"Response: {response.text}")
                return False
        except Exception as e:
            print(f"❌ FileMaker connection error: {e}")
            return False
    
    def insert_po_data(self, po_info):
        """Insert PO data into FileMaker database and trigger PDFTimesheet script"""
        if not self.token:
            if not self.authenticate():
                return False
        
        # Create record in PreInventory layout first (for inventory tracking)
        preinventory_data = {
            "fieldData": {
                "Whittaker Shipper #": str(po_info.get("purchase_order_number", "")),  # Purchase Order # field
                "IncomingPO": str(po_info.get("purchase_order_number", "")),           # Also populate backup field
                "MJO NO": str(po_info.get("production_order", "")),                    # Work Order
                "PART NUMBER": str(po_info.get("part_number", "")),                    # Part Number
                "QTY SHIP": int(po_info.get("quantity", 0)) if po_info.get("quantity") else 0,  # Quantity
                "IncomingRouter": str(po_info.get("source_file", "")),                # Source PDF file
                "Revision": str(po_info.get("revision", ""))                          # Part Revision
            }
        }
        
        # Add Planner Name only if it's not a test value that would fail validation
        buyer_name = po_info.get("buyer_name", "")
        if buyer_name and buyer_name not in ["Test Buyer", "Buyer"]:  # Exclude common test values
            preinventory_data["fieldData"]["Planner Name"] = str(buyer_name)
        
        headers = {
            'Authorization': f'Bearer {self.token}',
            'Content-Type': 'application/json'
        }
        
        # Insert to PreInventory layout
        preinventory_url = f"{self.server}/fmi/data/v1/databases/{self.database}/layouts/{self.layout}/records"
        
        try:
            # Create PreInventory record and call PDFTimesheet script in the same request
            po_number = po_info.get('purchase_order_number', 'Unknown')
            
            # Add script execution to the PreInventory record creation
            preinventory_data_with_script = {
                "fieldData": preinventory_data["fieldData"],
                "script": "PDFTimesheet",
                "script.param": po_number
            }
            
            preinventory_response = requests.post(preinventory_url, json=preinventory_data_with_script, headers=headers, verify=False)
            
            if preinventory_response.status_code == 200:
                response_data = preinventory_response.json().get('response', {})
                preinventory_record_id = response_data.get('recordId')
                script_error = response_data.get('scriptError', '0')
                script_result = response_data.get('scriptResult', 'No result')
                
                print(f"✅ PO {po_info.get('purchase_order_number')} inserted to PreInventory (Record ID: {preinventory_record_id})")
                
                # Report PDFTimesheet script execution status
                if script_error == '0':
                    print(f"✅ PDFTimesheet script executed successfully during PreInventory record creation")
                    print(f"📄 PDF should be generated at: filemac:/Macintosh HD/Users/Shared/ParkerPOsOCR/exports/{po_number}.pdf")
                    print(f"   (Mac filesystem: /Users/Shared/ParkerPOsOCR/exports/{po_number}.pdf)")
                    print(f"⚠️ Note: PreInventory record {preinventory_record_id} may have been deleted by script (normal behavior)")
                    if script_result and script_result != 'No result':
                        print(f"   📄 Script result: {script_result}")
                else:
                    print(f"⚠️ PDFTimesheet script error code: {script_error}")
                    if script_result:
                        print(f"   📄 Script result: {script_result}")
                    self._log_script_error(script_error)
                
                return True
            else:
                print(f"⚠️ PreInventory insert (with script) failed: {preinventory_response.status_code} - {preinventory_response.text}")
                return False
                
        except Exception as e:
            print(f"❌ FileMaker insert error: {e}")
            return False
    
    def _log_script_error(self, error_code):
        """Log PDFTimesheet script error with troubleshooting info"""
        error_meanings = {
            '102': 'Field missing or invalid - check if required fields have data',
            '401': 'No records match the request - script may be looking for missing records',
            '506': 'Field validation error - check field constraints', 
            '800': 'Unable to create file on disk - check FileMaker Server permissions',
            '801': 'Unable to create temporary file - check disk space',
            '802': 'Unable to open file - check file paths and permissions'
        }
        error_msg = error_meanings.get(error_code, f'Unknown script error code {error_code}')
        print(f"   Error details: {error_msg}")
        
        if error_code in ['800', '801', '802']:
            print("   💡 PDF generation issue - check FileMaker Server file system permissions")
            print("   📁 Mac Server PDF path: /Users/Shared/ParkerPOsOCR/exports/")
    
    def print_pdf_on_mac(self, po_number):
        """Print PDF on Mac using SSH and lp command"""
        import subprocess
        import time
        
        pdf_path = f"/Users/Shared/ParkerPOsOCR/exports/{po_number}.pdf"
        mac_host = "192.168.0.105"
        ssh_user = "Anthony"
        
        # Wait a moment for PDF to be fully written
        time.sleep(2)
        
        try:
            # Use SSH to execute print command on Mac
            ssh_command = f'ssh {ssh_user}@{mac_host} "lp \\"{pdf_path}\\""'
            print(f"🖨️ Sending PDF to printer: {pdf_path}")
            
            # Note: This requires SSH key authentication or manual password entry
            # For automation, you'd need to set up SSH keys
            result = subprocess.run(ssh_command, shell=True, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                print(f"✅ PDF sent to default printer successfully")
                print(f"   Print job output: {result.stdout.strip()}")
                return True
            else:
                print(f"⚠️ Print command returned error: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            print("⚠️ Print command timed out - may require manual password entry")
            return False
        except Exception as e:
            print(f"❌ Print error: {str(e)}")
            return False
    
    def check_pdf_generated(self, po_number):
        """Check if PDF was generated on Mac FileMaker Server (informational only)"""
        expected_path = f"/Users/Shared/ParkerPOsOCR/exports/{po_number}.pdf"
        print(f"💡 To verify PDF generation, check Mac FileMaker Server at:")
        print(f"   📁 {expected_path}")
        print(f"   🔧 You can also check via FileMaker Server Admin Console or SSH to server")
    
    def check_duplicate_po(self, po_number):
        """Check if PO already exists in FileMaker"""
        if not self.token:
            if not self.authenticate():
                return False
        
        url = f"{self.server}/fmi/data/v1/databases/{self.database}/layouts/{self.layout}/_find"
        
        find_request = {
            "query": [
                {"IncomingPO": po_number}
            ]
        }
        
        headers = {
            'Authorization': f'Bearer {self.token}',
            'Content-Type': 'application/json'
        }
        
        try:
            response = requests.post(url, json=find_request, headers=headers, verify=False)
            if response.status_code == 200:
                records = response.json().get('response', {}).get('data', [])
                return len(records) > 0
            else:
                return False
        except Exception as e:
            print(f"❌ FileMaker duplicate check error: {e}")
            return False
    
    def logout(self):
        """Logout from FileMaker Data API"""
        if self.token:
            url = f"{self.server}/fmi/data/v1/databases/{self.database}/sessions/{self.token}"
            try:
                requests.delete(url, verify=False)
                print("✅ FileMaker session closed")
            except Exception as e:
                print(f"❌ FileMaker disconnect error: {e}")

# Example usage for integration into your pipeline
def integrate_with_filemaker(po_folder_path):
    """
    Integration function to be called after PO processing
    Add this to your process_po_complete.py
    """
    fm = FileMakerIntegration()
    
    # Read the processed JSON file
    json_file = os.path.join(po_folder_path, f"{os.path.basename(po_folder_path)}_info.json")
    
    if not os.path.exists(json_file):
        print(f"❌ JSON file not found: {json_file}")
        return False
    
    try:
        with open(json_file, 'r') as f:
            po_info = json.load(f)
        
        po_number = po_info.get("purchase_order_number")
        
        # Check for duplicates
        if fm.check_duplicate_po(po_number):
            print(f"⚠️  PO {po_number} already exists in FileMaker - skipping")
            return True
        
        # Insert new PO
        success = fm.insert_po_data(po_info)
        
        if success:
            print(f"🖨️ Attempting to print PDF for PO {po_number}...")
            fm.print_pdf_on_mac(po_number)
        
        fm.disconnect()
        
        return success
        
    except Exception as e:
        print(f"❌ FileMaker integration error: {e}")
        return False

if __name__ == "__main__":
    # Test the connection
    fm = FileMakerIntegration()
    if fm.authenticate():
        print("FileMaker Data API connection test successful!")
        fm.disconnect()
    else:
        print("FileMaker Data API connection test failed!")