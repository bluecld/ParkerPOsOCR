#!/usr/bin/env python3
"""
PDFTimesheet Script Diagnostic Tool
Helps troubleshoot why PDFTimesheet script isn't generating PDFs as expected
"""

import requests
import json
import os
import base64
import urllib3
from urllib.parse import urlparse
from datetime import datetime

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class PDFTimesheetDiagnostic:
    def __init__(self):
        self.server = os.getenv('FILEMAKER_SERVER', 'https://192.168.0.105:443')
        self.database = os.getenv('FILEMAKER_DATABASE', 'PreInventory')
        self.username = os.getenv('FILEMAKER_USERNAME', 'JSON')
        self.password = os.getenv('FILEMAKER_PASSWORD')
        self.token = None
        
        # Parse server URL
        parsed_url = urlparse(self.server)
        self.server_base = f'{parsed_url.scheme}://{parsed_url.netloc}'
        
    def authenticate(self):
        """Authenticate with FileMaker Data API"""
        credentials = f"{self.username}:{self.password}"
        encoded_credentials = base64.b64encode(credentials.encode('utf-8')).decode('utf-8')
        
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Basic {encoded_credentials}'
        }
        
        url = f"{self.server_base}/fmi/data/vLatest/databases/{self.database}/sessions"
        
        try:
            response = requests.post(url, json={}, headers=headers, verify=False)
            if response.status_code == 200:
                self.token = response.json()['response']['token']
                return True
            else:
                print(f"❌ Authentication failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Authentication error: {e}")
            return False
    
    def get_layouts(self):
        """Get all available layouts to see which ones might be suitable for PDFTimesheet"""
        if not self.token:
            return []
            
        headers = {
            'Authorization': f'Bearer {self.token}',
            'Content-Type': 'application/json'
        }
        
        url = f"{self.server_base}/fmi/data/vLatest/databases/{self.database}/layouts"
        
        try:
            response = requests.get(url, headers=headers, verify=False)
            if response.status_code == 200:
                layouts = response.json().get('response', {}).get('layouts', [])
                return [layout.get('name') for layout in layouts]
            return []
        except Exception as e:
            print(f"❌ Error getting layouts: {e}")
            return []
    
    def test_script_on_layout(self, layout_name, record_data):
        """Test PDFTimesheet script on a specific layout"""
        if not self.token:
            return None
            
        headers = {
            'Authorization': f'Bearer {self.token}',
            'Content-Type': 'application/json'
        }
        
        # Create record on specific layout
        create_url = f"{self.server_base}/fmi/data/vLatest/databases/{self.database}/layouts/{layout_name}/records"
        
        create_payload = {
            'fieldData': record_data
        }
        
        try:
            create_response = requests.post(create_url, json=create_payload, headers=headers, verify=False)
            
            if create_response.status_code == 200:
                record_id = create_response.json().get('response', {}).get('recordId')
                print(f"✅ Created record {record_id} on layout '{layout_name}'")
                
                # Execute PDFTimesheet script
                update_url = f"{self.server_base}/fmi/data/vLatest/databases/{self.database}/layouts/{layout_name}/records/{record_id}"
                
                script_payload = {
                    'fieldData': {},
                    'script': 'PDFTimesheet'
                }
                
                script_response = requests.patch(update_url, json=script_payload, headers=headers, verify=False)
                
                if script_response.status_code == 200:
                    result = script_response.json().get('response', {})
                    script_result = result.get('scriptResult', 'No result')
                    script_error = result.get('scriptError', '0')
                    
                    print(f"📋 Layout '{layout_name}' results:")
                    print(f"  Script Result: \"{script_result}\"")
                    print(f"  Script Error: {script_error}")
                    
                    # Clean up
                    delete_url = f"{self.server_base}/fmi/data/vLatest/databases/{self.database}/layouts/{layout_name}/records/{record_id}"
                    requests.delete(delete_url, headers=headers, verify=False)
                    
                    return {
                        'layout': layout_name,
                        'script_result': script_result,
                        'script_error': script_error,
                        'record_id': record_id
                    }
                else:
                    print(f"❌ Script execution failed on '{layout_name}': {script_response.text}")
                    
            else:
                print(f"❌ Failed to create record on '{layout_name}': {create_response.text}")
                
        except Exception as e:
            print(f"❌ Error testing layout '{layout_name}': {e}")
            
        return None
    
    def test_with_script_parameter(self, layout_name, record_id, parameter):
        """Test PDFTimesheet with a script parameter"""
        if not self.token:
            return None
            
        headers = {
            'Authorization': f'Bearer {self.token}',
            'Content-Type': 'application/json'
        }
        
        # Try different parameter formats that FileMaker scripts might expect
        parameter_formats = [
            parameter,
            json.dumps({"recordId": record_id, "action": "generatePDF"}),
            f"recordId={record_id}",
            str(record_id)
        ]
        
        results = []
        
        for param_format in parameter_formats:
            print(f"\n🔧 Testing parameter format: {param_format}")
            
            url = f"{self.server_base}/fmi/data/vLatest/databases/{self.database}/layouts/{layout_name}/records/{record_id}"
            
            # Use different methods to pass parameters
            methods = [
                {"script": "PDFTimesheet", "script.param": param_format},
                {"script": "PDFTimesheet"}  # No parameter
            ]
            
            for method in methods:
                payload = {
                    'fieldData': {},
                    **method
                }
                
                try:
                    response = requests.patch(url, json=payload, headers=headers, verify=False)
                    
                    if response.status_code == 200:
                        result = response.json().get('response', {})
                        script_result = result.get('scriptResult', 'No result')
                        script_error = result.get('scriptError', '0')
                        
                        results.append({
                            'parameter': param_format,
                            'method': str(method),
                            'script_result': script_result,
                            'script_error': script_error
                        })
                        
                        print(f"  ✅ Method {method}: Result='{script_result}', Error={script_error}")
                        
                    else:
                        print(f"  ❌ Method {method}: Failed with {response.status_code}")
                        
                except Exception as e:
                    print(f"  ❌ Method {method}: Exception {e}")
        
        return results
    
    def run_comprehensive_diagnostic(self):
        """Run comprehensive PDFTimesheet diagnostic"""
        print("🔍 Starting PDFTimesheet Script Comprehensive Diagnostic")
        print("=" * 60)
        
        if not self.authenticate():
            print("❌ Authentication failed - cannot proceed")
            return
            
        # Get all available layouts
        print("\n📋 Getting available layouts...")
        layouts = self.get_layouts()
        
        if layouts:
            print(f"Found {len(layouts)} layouts:")
            for layout in layouts[:10]:  # Show first 10
                print(f"  - {layout}")
                
            # Look for Time Clock or timesheet-related layouts
            timesheet_layouts = [layout for layout in layouts 
                               if any(keyword in layout.lower() 
                                    for keyword in ['time', 'timesheet', 'clock', 'labor', 'hours'])]
            
            if timesheet_layouts:
                print(f"\n🎯 Found timesheet-related layouts: {timesheet_layouts}")
            else:
                print("\n⚠️ No obvious timesheet-related layouts found")
        
        # Test script on different layouts with comprehensive record data
        test_data = {
            # PreInventory fields
            'Whittaker Shipper #': '4551888888',
            'IncomingPO': '4551888888',
            'MJO NO': '125888888',
            'PART NUMBER': 'DIAGNOSTIC_PART',
            'QTY SHIP': 10,
            'Planner Name': 'Daniel Rodriguez',
            'Revision': 'A',
            'IncomingRouter': 'diagnostic_test.pdf',
            
            # Potential timesheet fields that might be needed
            'Employee': 'Test Employee',
            'Hours': 8.0,
            'Date': datetime.now().strftime('%m/%d/%Y'),
            'Task': 'PDF Generation Test',
            'Department': 'Production',
            'Supervisor': 'Test Supervisor'
        }
        
        # Test on PreInventory layout first
        print(f"\n🔧 Testing PDFTimesheet on PreInventory layout...")
        result = self.test_script_on_layout('PreInventory', test_data)
        
        # If we found timesheet layouts, test those too
        for layout in timesheet_layouts[:3]:  # Test up to 3 timesheet layouts
            print(f"\n🔧 Testing PDFTimesheet on {layout} layout...")
            result = self.test_script_on_layout(layout, test_data)
            
        # Test BK_PDFTimesheet script as well
        print(f"\n🔧 Testing backup script BK_PDFTimesheet...")
        headers = {
            'Authorization': f'Bearer {self.token}',
            'Content-Type': 'application/json'
        }
        
        # Create a test record for backup script testing
        create_url = f"{self.server_base}/fmi/data/vLatest/databases/{self.database}/layouts/PreInventory/records"
        create_response = requests.post(create_url, json={'fieldData': test_data}, headers=headers, verify=False)
        
        if create_response.status_code == 200:
            record_id = create_response.json().get('response', {}).get('recordId')
            
            update_url = f"{self.server_base}/fmi/data/vLatest/databases/{self.database}/layouts/PreInventory/records/{record_id}"
            backup_payload = {
                'fieldData': {},
                'script': 'BK_PDFTimesheet'
            }
            
            backup_response = requests.patch(update_url, json=backup_payload, headers=headers, verify=False)
            
            if backup_response.status_code == 200:
                backup_result = backup_response.json().get('response', {})
                print(f"BK_PDFTimesheet Result: \"{backup_result.get('scriptResult', 'No result')}\"")
                print(f"BK_PDFTimesheet Error: {backup_result.get('scriptError', '0')}")
            
            # Clean up
            requests.delete(update_url, headers=headers, verify=False)
        
        print("\n" + "=" * 60)
        print("🎯 DIAGNOSTIC SUMMARY & RECOMMENDATIONS:")
        print("\n1. If all scripts return Error Code 0 with 'No result':")
        print("   - Script executes but has internal conditions not met")
        print("   - May need related records or specific field values")
        print("   - Could be designed for interactive use only")
        
        print("\n2. If specific layouts work better:")
        print("   - PDFTimesheet may be designed for Time Clock layout")
        print("   - Consider running script in correct layout context")
        
        print("\n3. Next troubleshooting steps:")
        print("   - Check FileMaker Pro script steps for PDFTimesheet")
        print("   - Look for 'Go to Layout' or 'Enter Browse Mode' steps")
        print("   - Check for 'Show Custom Dialog' or user interaction steps")
        print("   - Verify PDF output directory and permissions")
        
        # Close session
        url = f"{self.server_base}/fmi/data/vLatest/databases/{self.database}/sessions/{self.token}"
        requests.delete(url, headers=headers, verify=False)

if __name__ == "__main__":
    diagnostic = PDFTimesheetDiagnostic()
    diagnostic.run_comprehensive_diagnostic()
