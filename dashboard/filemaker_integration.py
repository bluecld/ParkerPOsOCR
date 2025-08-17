# FileMaker ERP Integration Module
# Prepares PO data for FileMaker Data API integration

import json
import os
import requests
from datetime import datetime
from pathlib import Path

class FileMakerIntegration:
    """FileMaker ERP Integration for PO Processing System"""
    
    def __init__(self, server_url, database, username, password, ssl_verify=True, timeout=30):
        self.server_url = server_url.rstrip('/')
        self.database = database
        self.username = username
        self.password = password
        self.ssl_verify = ssl_verify
        self.timeout = timeout
        self.token = None
        self.base_path = "/volume1/Main/Main/ParkerPOsOCR"
    
    def authenticate(self):
        """Authenticate with FileMaker Data API"""
        try:
            auth_url = f"{self.server_url}/fmi/data/v1/databases/{self.database}/sessions"
            print(f"DEBUG: Authenticating to {auth_url}")
            
            # FileMaker Data API expects Basic Authentication
            import base64
            credentials = base64.b64encode(f"{self.username}:{self.password}".encode()).decode()
            
            headers = {
                'Authorization': f'Basic {credentials}',
                'Content-Type': 'application/json'
            }
            
            print(f"DEBUG: Sending POST request with timeout={self.timeout}s, ssl_verify={self.ssl_verify}")
            
            # Use a shorter timeout for initial connection test
            import requests
            from requests.exceptions import ConnectTimeout, ConnectionError, Timeout
            
            try:
                response = requests.post(
                    auth_url, 
                    headers=headers, 
                    json={}, 
                    verify=self.ssl_verify, 
                    timeout=self.timeout
                )
                
                print(f"DEBUG: Received response with status code: {response.status_code}")
                
                if response.status_code == 200:
                    result = response.json()
                    self.token = result.get('response', {}).get('token')
                    print(f"DEBUG: Authentication successful, token received")
                    return True
                else:
                    print(f"Authentication failed: {response.status_code} - {response.text}")
                    return False
                    
            except (ConnectTimeout, ConnectionError, Timeout) as conn_error:
                print(f"Connection error to FileMaker server: {conn_error}")
                print(f"Check if FileMaker server at {self.server_url} is accessible")
                return False
                
        except Exception as e:
            print(f"Authentication error: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def get_headers(self):
        """Get headers for FileMaker API requests"""
        return {
            'Authorization': f'Bearer {self.token}',
            'Content-Type': 'application/json'
        }
    
    def prepare_po_data(self, po_folder_path):
        """Prepare PO data for FileMaker import"""
        po_data = {
            "timestamp": datetime.now().isoformat(),
            "po_folder": os.path.basename(po_folder_path),
            "extracted_data": {},
            "files": {
                "json_files": [],
                "pdf_files": [],
                "images": []
            },
            "processing_info": {}
        }
        
        # Load JSON data files
        json_files = list(Path(po_folder_path).glob("*.json"))
        for json_file in json_files:
            try:
                with open(json_file, 'r') as f:
                    data = json.load(f)
                    po_data["extracted_data"][json_file.stem] = data
                    po_data["files"]["json_files"].append({
                        "filename": json_file.name,
                        "path": str(json_file),
                        "size": json_file.stat().st_size
                    })
            except Exception as e:
                print(f"Error reading {json_file}: {e}")
        
        # List PDF files
        pdf_files = list(Path(po_folder_path).glob("*.pdf"))
        for pdf_file in pdf_files:
            po_data["files"]["pdf_files"].append({
                "filename": pdf_file.name,
                "path": str(pdf_file),
                "size": pdf_file.stat().st_size,
                "created": datetime.fromtimestamp(pdf_file.stat().st_ctime).isoformat()
            })
        
        # List image files
        image_extensions = ['.jpg', '.jpeg', '.png', '.tiff', '.bmp']
        for ext in image_extensions:
            image_files = list(Path(po_folder_path).glob(f"*{ext}"))
            for image_file in image_files:
                po_data["files"]["images"].append({
                    "filename": image_file.name,
                    "path": str(image_file),
                    "size": image_file.stat().st_size
                })
        
        return po_data
    
    def create_record(self, field_data, layout_name="PreInventory", config=None):
        """Create a record in FileMaker with direct field data and trigger lookups"""
        if not self.token:
            if not self.authenticate():
                return False
        
        try:
            create_url = f"{self.server_url}/fmi/data/v1/databases/{self.database}/layouts/{layout_name}/records"
            
            # Clean and validate field data
            cleaned_data = {}
            for field_name, value in field_data.items():
                if value is not None and str(value).strip():
                    # Clean specific fields that might have validation issues
                    if field_name == "QTY SHIP":
                        # Ensure quantity is a string, not integer (FileMaker validation issue)
                        cleaned_data[field_name] = str(value)
                    elif field_name == "Promise Delivery Date":
                        # Ensure date is in proper format
                        if isinstance(value, str) and len(value) > 0:
                            cleaned_data[field_name] = value
                    elif field_name == "Planner Name":
                        # Clean planner name for validation
                        cleaned_value = str(value).strip()
                        if cleaned_value:
                            cleaned_data[field_name] = cleaned_value
                    else:
                        cleaned_data[field_name] = str(value).strip()
            
            payload = {
                "fieldData": cleaned_data
            }
            
            # Debug: Print what we're sending to FileMaker
            print(f"Sending to FileMaker: {payload}")
            
            # Add script execution to trigger lookups if configured
            if config and config.get('trigger_lookups', False):
                script_name = config.get('lookup_script', None)
                if script_name:
                    # Use the proper FileMaker Data API script execution method
                    payload["script"] = script_name
                    # Pass both PO number and Part Number as script parameter for better targeting
                    po_number = cleaned_data.get('Whittaker Shipper #', '')
                    part_number = cleaned_data.get('PART NUMBER', '')
                    script_param = f"{po_number}|{part_number}"  # Pass both values separated by |
                    payload["script.param"] = script_param
                    print(f"Adding lookup script to payload: {script_name} with param: {script_param}")
            
            response = requests.post(create_url, json=payload, headers=self.get_headers(), verify=self.ssl_verify, timeout=self.timeout)
            
            # Debug: Print FileMaker response
            print(f"FileMaker response: {response.status_code} - {response.text}")
            
            if response.status_code == 200 or response.status_code == 201:
                result = response.json()
                record_id = result.get('response', {}).get('recordId')
                print(f"Record created successfully with ID: {record_id}")
                
                # Check if script executed successfully
                script_result = result.get('response', {}).get('scriptResult')
                if script_result is not None:
                    print(f"Lookup script result: {script_result}")
                
                # Simulate lookups by manually retrieving related data and updating fields
                if record_id and config and config.get('trigger_lookups', False):
                    print(f"Simulating lookups by retrieving related data from PRICES database")
                    self.simulate_lookups_via_related_data(record_id, cleaned_data, layout_name, config)
                
                return record_id
            else:
                # Handle specific FileMaker validation errors
                try:
                    error_response = response.json()
                    messages = error_response.get('messages', [])
                    for msg in messages:
                        error_code = msg.get('code')
                        error_message = msg.get('message')
                        
                        if error_code == '504':
                            # Handle duplicate record error
                            po_number = cleaned_data.get('Whittaker Shipper #', 'Unknown')
                            print(f"⚠️ Duplicate PO record: PO {po_number} already exists in FileMaker database")
                            print("This is not necessarily an error - the PO may have been processed before.")
                            
                            # Try to find and update the existing record instead
                            existing_record_id = self.find_existing_record(po_number, layout_name)
                            if existing_record_id:
                                print(f"Found existing record {existing_record_id}, attempting to update...")
                                updated = self.update_existing_record(existing_record_id, cleaned_data, layout_name)
                                if updated:
                                    print(f"✅ Successfully updated existing record {existing_record_id}")
                                    return existing_record_id
                                else:
                                    print(f"⚠️ Could not update existing record, but record exists")
                                    return existing_record_id  # Return existing ID even if update failed
                            else:
                                print(f"⚠️ Duplicate error but couldn't find existing record. Skipping.")
                                return "DUPLICATE_SKIP"  # Special return value to indicate handled duplicate
                        elif error_code == '506':
                            print(f"FileMaker validation error: {error_message}")
                            print("This usually means a field value is not in the allowed list")
                            print(f"Check FileMaker field validation for: {list(cleaned_data.keys())}")
                        else:
                            print(f"FileMaker error {error_code}: {error_message}")
                except:
                    pass
                
                print(f"Failed to create record: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"Error creating FileMaker record: {e}")
            return False

    def simple_lookup_trigger(self, record_id, field_data, layout_name, config):
        """Simple approach to trigger lookups by updating one field at a time"""
        if not self.token:
            return False
        
        try:
            update_url = f"{self.server_url}/fmi/data/v1/databases/{self.database}/layouts/{layout_name}/records/{record_id}"
            lookup_fields = config.get('lookup_fields', [])
            
            # Update each lookup field individually to trigger lookups
            for field_name in lookup_fields:
                if field_name in field_data:
                    # Update just this one field
                    single_field_data = {field_name: field_data[field_name]}
                    payload = {
                        "fieldData": single_field_data
                    }
                    
                    response = requests.patch(update_url, json=payload, headers=self.get_headers(), verify=self.ssl_verify, timeout=self.timeout)
                    
                    if response.status_code == 200:
                        print(f"Lookup triggered for field {field_name}")
                    else:
                        print(f"Failed to trigger lookup for {field_name}: {response.status_code}")
                        
        except Exception as e:
            print(f"Error in simple lookup trigger: {e}")

    def trigger_lookups_via_field_update(self, record_id, field_data, layout_name="PreInventory"):
        """
        Trigger FileMaker lookups by updating the Part Number field via Data API
        This approach uses FileMaker's automatic lookup mechanism when match fields are updated
        """
        if not self.token:
            print("No authentication token available")
            return False
        
        try:
            update_url = f"{self.server_url}/fmi/data/v1/databases/{self.database}/layouts/{layout_name}/records/{record_id}"
            part_number = field_data.get('PART NUMBER', '')
            
            if not part_number:
                print("No Part Number found to trigger lookups")
                return False
            
            print(f"Triggering lookups for Part Number: {part_number}")
            
            # Step 1: Clear the Part Number field first (this resets any existing lookups)
            clear_payload = {
                "fieldData": {
                    "PART NUMBER": ""
                }
            }
            
            print("Step 1: Clearing Part Number field...")
            clear_response = requests.patch(
                update_url, 
                json=clear_payload, 
                headers=self.get_headers(), 
                verify=self.ssl_verify, 
                timeout=self.timeout
            )
            
            if clear_response.status_code == 200:
                print("✅ Part Number field cleared successfully")
            else:
                print(f"⚠️ Warning: Could not clear Part Number field: {clear_response.status_code}")
            
            # Step 2: Set the Part Number field (this triggers automatic lookups)
            set_payload = {
                "fieldData": {
                    "PART NUMBER": part_number
                }
            }
            
            print(f"Step 2: Setting Part Number to '{part_number}'...")
            set_response = requests.patch(
                update_url, 
                json=set_payload, 
                headers=self.get_headers(), 
                verify=self.ssl_verify, 
                timeout=self.timeout
            )
            
            if set_response.status_code == 200:
                print("✅ Part Number field updated successfully")
                
                # Get the updated record to verify lookups worked
                updated_record = self.get_record(record_id, layout_name)
                if updated_record:
                    field_data = updated_record.get('fieldData', {})
                    print("\n📋 Lookup Results:")
                    print(f"  Part Number: {field_data.get('PART NUMBER', 'EMPTY')}")
                    print(f"  Description: {field_data.get('Description', 'EMPTY')}")
                    print(f"  Revision: {field_data.get('Revision', 'EMPTY')}")
                    print(f"  Op Sheet Issue: {field_data.get('Op Sheet Issue', 'EMPTY')}")
                    
                    # Check if lookups worked
                    if field_data.get('Description') or field_data.get('Revision'):
                        print("✅ SUCCESS: Lookups populated!")
                        return True
                    else:
                        print("❌ WARNING: Lookup fields still empty")
                        return False
                else:
                    print("Could not retrieve updated record for verification")
                    return True  # Assume success if we can't verify
                    
            else:
                print(f"❌ Failed to update Part Number field: {set_response.status_code} - {set_response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Error triggering lookups via field update: {e}")
            import traceback
            traceback.print_exc()
            return False

    def simulate_lookups_via_related_data(self, record_id, field_data, layout_name="PreInventory", config=None):
        """
        Simulate FileMaker lookups by manually retrieving data from related tables
        This approach handles PRICES being in the same or different database
        1. Find related record in PRICES table based on Part Number
        2. Retrieve Description, Revision, Op Sheet Issue from the related record
        3. Update the current record with the retrieved data
        """
        if not self.token:
            print("No authentication token available")
            return False
        
        try:
            part_number = field_data.get('PART NUMBER', '')
            
            if not part_number:
                print("No Part Number found to perform lookup")
                return False
            
            print(f"🔍 Simulating lookup for Part Number: {part_number}")
            
            # Get PRICES database configuration
            prices_database = config.get('prices_database', 'PreInventory') if config else 'PreInventory'
            prices_layout = config.get('prices_layout', 'PRICES') if config else 'PRICES'
            
            print(f"🗄️ Searching in database: {prices_database}, layout: {prices_layout}")
            
            # Check if we need to authenticate to a different database
            if prices_database == self.database:
                # Same database - use existing token
                print("✅ Using existing authentication (same database)")
                prices_token = self.token
                prices_headers = self.get_headers()
                need_logout = False
            else:
                # Different database - need separate authentication
                print(f"🔐 Authenticating to separate PRICES database: {prices_database}")
                
                prices_auth_url = f"{self.server_url}/fmi/data/v1/databases/{prices_database}/sessions"
                
                import base64
                credentials = base64.b64encode(f"{self.username}:{self.password}".encode()).decode()
                
                headers = {
                    'Authorization': f'Basic {credentials}',
                    'Content-Type': 'application/json'
                }
                
                prices_auth_response = requests.post(
                    prices_auth_url, 
                    headers=headers, 
                    json={}, 
                    verify=self.ssl_verify, 
                    timeout=self.timeout
                )
                
                if prices_auth_response.status_code == 200:
                    prices_result = prices_auth_response.json()
                    prices_token = prices_result.get('response', {}).get('token')
                    
                    if not prices_token:
                        print("❌ Failed to get authentication token for PRICES database")
                        return False
                    
                    print("✅ Successfully authenticated to PRICES database")
                    
                    prices_headers = {
                        'Authorization': f'Bearer {prices_token}',
                        'Content-Type': 'application/json'
                    }
                    need_logout = True
                else:
                    print(f"❌ Failed to authenticate to PRICES database: {prices_auth_response.status_code} - {prices_auth_response.text}")
                    return False
            
            # Step 2: Find related record in PRICES table
            find_url = f"{self.server_url}/fmi/data/v1/databases/{prices_database}/layouts/{prices_layout}/_find"
            
            # Search for the part number in the PRICES table
            find_payload = {
                "query": [
                    {
                        "Part Number": part_number  # Field name in PRICES table
                    }
                ]
            }
            
            print(f"🔍 Searching PRICES table for Part Number: {part_number}")
            
            find_response = requests.post(
                find_url, 
                json=find_payload, 
                headers=prices_headers, 
                verify=self.ssl_verify, 
                timeout=self.timeout
            )
            
            if find_response.status_code == 200:
                find_result = find_response.json()
                records = find_result.get('response', {}).get('data', [])
                
                if records:
                    # Get the first matching record from PRICES table
                    prices_record = records[0]
                    prices_fields = prices_record.get('fieldData', {})
                    
                    # Extract the lookup values using the correct field names from PRICES table
                    description = prices_fields.get('Description', '')
                    revision = prices_fields.get('Revision', '')
                    op_sheet_issue = prices_fields.get('Op Sheet Issue', '')
                    
                    print(f"✅ Found related record in PRICES table:")
                    print(f"   Description: {description}")
                    print(f"   Revision: {revision}")
                    print(f"   Op Sheet Issue: {op_sheet_issue}")
                    
                    # Step 3: Update the current record in PreInventory with the lookup data
                    update_url = f"{self.server_url}/fmi/data/v1/databases/{self.database}/layouts/{layout_name}/records/{record_id}"
                    
                    update_payload = {
                        "fieldData": {
                            "Description": description,
                            "Revision": revision,
                            "Op Sheet Issue": op_sheet_issue
                        }
                    }
                    
                    print(f"📝 Updating record {record_id} with lookup data...")
                    
                    update_response = requests.patch(
                        update_url, 
                        json=update_payload, 
                        headers=self.get_headers(),  # Use original database headers
                        verify=self.ssl_verify, 
                        timeout=self.timeout
                    )
                    
                    if update_response.status_code == 200:
                        print("✅ Successfully updated record with lookup data!")
                        
                        # Verify the update
                        updated_record = self.get_record(record_id, layout_name)
                        if updated_record:
                            final_fields = updated_record.get('fieldData', {})
                            print("\n📋 Final Record State:")
                            print(f"  Part Number: {final_fields.get('PART NUMBER', 'EMPTY')}")
                            print(f"  Description: {final_fields.get('Description', 'EMPTY')}")
                            print(f"  Revision: {final_fields.get('Revision', 'EMPTY')}")
                            print(f"  Op Sheet Issue: {final_fields.get('Op Sheet Issue', 'EMPTY')}")
                            
                            if final_fields.get('Description') and final_fields.get('Revision'):
                                print("🎉 SUCCESS: Lookup simulation completed successfully!")
                                success = True
                            else:
                                print("⚠️ WARNING: Fields updated but values appear empty")
                                success = False
                        else:
                            print("Could not verify the update")
                            success = True  # Assume success
                    else:
                        print(f"❌ Failed to update record with lookup data: {update_response.status_code} - {update_response.text}")
                        success = False
                        
                else:
                    print(f"❌ No matching record found in PRICES table for Part Number: {part_number}")
                    print("   This means the part number doesn't exist in the PRICES table")
                    success = False
                    
            elif find_response.status_code == 401:
                print("❌ No records found or access denied to PRICES layout")
                print("   Check if the PRICES layout exists and is accessible")
                success = False
            else:
                print(f"❌ Failed to search PRICES table: {find_response.status_code} - {find_response.text}")
                success = False
            
            # Cleanup: logout from PRICES database if we authenticated separately
            if need_logout and prices_token:
                logout_url = f"{self.server_url}/fmi/data/v1/databases/{prices_database}/sessions/{prices_token}"
                requests.delete(logout_url, headers=prices_headers, verify=self.ssl_verify, timeout=self.timeout)
                print("🔐 Logged out from PRICES database")
            
            return success
                
        except Exception as e:
            print(f"❌ Error simulating lookups via related data: {e}")
            import traceback
            traceback.print_exc()
            return False
        """
        Simulate FileMaker lookups by manually retrieving data from related tables
        This approach handles PRICES being in a different database file
        1. Authenticate to PRICES database
        2. Find related record in PRICES table based on Part Number
        3. Retrieve Description, Revision, Op Sheet Issue from the related record
        4. Update the current record with the retrieved data
        """
        if not self.token:
            print("No authentication token available")
            return False
        
        try:
            part_number = field_data.get('PART NUMBER', '')
            
            if not part_number:
                print("No Part Number found to perform lookup")
                return False
            
            print(f"🔍 Simulating lookup for Part Number: {part_number}")
            
            # Get PRICES database configuration
            prices_database = config.get('prices_database', 'PRICES 7_9_2002') if config else 'PRICES 7_9_2002'
            prices_layout = config.get('prices_layout', 'PRICES') if config else 'PRICES'
            
            print(f"🗄️ Searching in PRICES database: {prices_database}")
            
            # Step 1: Authenticate to PRICES database (separate database)
            prices_auth_url = f"{self.server_url}/fmi/data/v1/databases/{prices_database}/sessions"
            
            import base64
            credentials = base64.b64encode(f"{self.username}:{self.password}".encode()).decode()
            
            headers = {
                'Authorization': f'Basic {credentials}',
                'Content-Type': 'application/json'
            }
            
            print(f"🔐 Authenticating to PRICES database...")
            
            prices_auth_response = requests.post(
                prices_auth_url, 
                headers=headers, 
                json={}, 
                verify=self.ssl_verify, 
                timeout=self.timeout
            )
            
            if prices_auth_response.status_code == 200:
                prices_result = prices_auth_response.json()
                prices_token = prices_result.get('response', {}).get('token')
                
                if not prices_token:
                    print("❌ Failed to get authentication token for PRICES database")
                    return False
                
                print("✅ Successfully authenticated to PRICES database")
                
                # Create headers for PRICES database requests
                prices_headers = {
                    'Authorization': f'Bearer {prices_token}',
                    'Content-Type': 'application/json'
                }
                
                # Step 2: Find related record in PRICES table
                find_url = f"{self.server_url}/fmi/data/v1/databases/{prices_database}/layouts/{prices_layout}/_find"
                
                # Search for the part number in the PRICES table
                find_payload = {
                    "query": [
                        {
                            "Part Number": part_number  # Field name in PRICES table
                        }
                    ]
                }
                
                print(f"🔍 Searching PRICES table for Part Number: {part_number}")
                
                find_response = requests.post(
                    find_url, 
                    json=find_payload, 
                    headers=prices_headers, 
                    verify=self.ssl_verify, 
                    timeout=self.timeout
                )
                
                if find_response.status_code == 200:
                    find_result = find_response.json()
                    records = find_result.get('response', {}).get('data', [])
                    
                    if records:
                        # Get the first matching record from PRICES table
                        prices_record = records[0]
                        prices_fields = prices_record.get('fieldData', {})
                        
                        # Extract the lookup values using the correct field names from PRICES table
                        description = prices_fields.get('Description', '')
                        revision = prices_fields.get('Revision', '')
                        op_sheet_issue = prices_fields.get('Op Sheet Issue', '')
                        
                        print(f"✅ Found related record in PRICES database:")
                        print(f"   Description: {description}")
                        print(f"   Revision: {revision}")
                        print(f"   Op Sheet Issue: {op_sheet_issue}")
                        
                        # Close PRICES database session
                        logout_url = f"{self.server_url}/fmi/data/v1/databases/{prices_database}/sessions/{prices_token}"
                        requests.delete(logout_url, headers=prices_headers, verify=self.ssl_verify, timeout=self.timeout)
                        
                        # Step 3: Update the current record in PreInventory database with the lookup data
                        update_url = f"{self.server_url}/fmi/data/v1/databases/{self.database}/layouts/{layout_name}/records/{record_id}"
                        
                        update_payload = {
                            "fieldData": {
                                "Description": description,
                                "Revision": revision,
                                "Op Sheet Issue": op_sheet_issue
                            }
                        }
                        
                        print(f"📝 Updating PreInventory record {record_id} with lookup data...")
                        
                        update_response = requests.patch(
                            update_url, 
                            json=update_payload, 
                            headers=self.get_headers(),  # Use PreInventory database headers
                            verify=self.ssl_verify, 
                            timeout=self.timeout
                        )
                        
                        if update_response.status_code == 200:
                            print("✅ Successfully updated record with lookup data!")
                            
                            # Verify the update
                            updated_record = self.get_record(record_id, layout_name)
                            if updated_record:
                                final_fields = updated_record.get('fieldData', {})
                                print("\n📋 Final Record State:")
                                print(f"  Part Number: {final_fields.get('PART NUMBER', 'EMPTY')}")
                                print(f"  Description: {final_fields.get('Description', 'EMPTY')}")
                                print(f"  Revision: {final_fields.get('Revision', 'EMPTY')}")
                                print(f"  Op Sheet Issue: {final_fields.get('Op Sheet Issue', 'EMPTY')}")
                                
                                if final_fields.get('Description') and final_fields.get('Revision'):
                                    print("🎉 SUCCESS: Cross-database lookup simulation completed successfully!")
                                    return True
                                else:
                                    print("⚠️ WARNING: Fields updated but values appear empty")
                                    return False
                            else:
                                print("Could not verify the update")
                                return True  # Assume success
                        else:
                            print(f"❌ Failed to update PreInventory record with lookup data: {update_response.status_code} - {update_response.text}")
                            return False
                            
                    else:
                        print(f"❌ No matching record found in PRICES database for Part Number: {part_number}")
                        print("   This means the part number doesn't exist in the PRICES table")
                        
                        # Close PRICES database session
                        logout_url = f"{self.server_url}/fmi/data/v1/databases/{prices_database}/sessions/{prices_token}"
                        requests.delete(logout_url, headers=prices_headers, verify=self.ssl_verify, timeout=self.timeout)
                        return False
                        
                elif find_response.status_code == 401:
                    print("❌ No records found or access denied to PRICES table")
                    print("   Check if the PRICES layout exists and is accessible")
                    
                    # Close PRICES database session
                    logout_url = f"{self.server_url}/fmi/data/v1/databases/{prices_database}/sessions/{prices_token}"
                    requests.delete(logout_url, headers=prices_headers, verify=self.ssl_verify, timeout=self.timeout)
                    return False
                else:
                    print(f"❌ Failed to search PRICES table: {find_response.status_code} - {find_response.text}")
                    
                    # Close PRICES database session
                    logout_url = f"{self.server_url}/fmi/data/v1/databases/{prices_database}/sessions/{prices_token}"
                    requests.delete(logout_url, headers=prices_headers, verify=self.ssl_verify, timeout=self.timeout)
                    return False
                    
            else:
                print(f"❌ Failed to authenticate to PRICES database: {prices_auth_response.status_code} - {prices_auth_response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Error simulating lookups via related data: {e}")
            import traceback
            traceback.print_exc()
            return False
        """
        Simulate FileMaker lookups by manually retrieving data from related tables
        This approach mimics what FileMaker's internal lookup mechanism would do:
        1. Find related record in PRICES table based on Part Number
        2. Retrieve Description, Revision, Op Sheet Issue from the related record
        3. Update the current record with the retrieved data
        """
        if not self.token:
            print("No authentication token available")
            return False
        
        try:
            part_number = field_data.get('PART NUMBER', '')
            
            if not part_number:
                print("No Part Number found to perform lookup")
                return False
            
            print(f"🔍 Simulating lookup for Part Number: {part_number}")
            
            # Step 1: Find related record in PRICES table
            prices_layout = "PRICES"  # Assuming the PRICES table has a layout with the same name
            find_url = f"{self.server_url}/fmi/data/v1/databases/{self.database}/layouts/{prices_layout}/_find"
            
            # Search for the part number in the PRICES table
            find_payload = {
                "query": [
                    {
                        "PART NUMBER": part_number  # Exact match search
                    }
                ]
            }
            
            print(f"🔍 Searching PRICES table for Part Number: {part_number}")
            
            find_response = requests.post(
                find_url, 
                json=find_payload, 
                headers=self.get_headers(), 
                verify=self.ssl_verify, 
                timeout=self.timeout
            )
            
            if find_response.status_code == 200:
                find_result = find_response.json()
                records = find_result.get('response', {}).get('data', [])
                
                if records:
                    # Get the first matching record from PRICES table
                    prices_record = records[0]
                    prices_fields = prices_record.get('fieldData', {})
                    
                    # Extract the lookup values
                    description = prices_fields.get('Description', '')
                    revision = prices_fields.get('Revision', '')
                    op_sheet_issue = prices_fields.get('Op Sheet Issue', '')
                    
                    print(f"✅ Found related record in PRICES table:")
                    print(f"   Description: {description}")
                    print(f"   Revision: {revision}")
                    print(f"   Op Sheet Issue: {op_sheet_issue}")
                    
                    # Step 2: Update the current record with the lookup data
                    update_url = f"{self.server_url}/fmi/data/v1/databases/{self.database}/layouts/{layout_name}/records/{record_id}"
                    
                    update_payload = {
                        "fieldData": {
                            "Description": description,
                            "Revision": revision,
                            "Op Sheet Issue": op_sheet_issue
                        }
                    }
                    
                    print(f"📝 Updating record {record_id} with lookup data...")
                    
                    update_response = requests.patch(
                        update_url, 
                        json=update_payload, 
                        headers=self.get_headers(), 
                        verify=self.ssl_verify, 
                        timeout=self.timeout
                    )
                    
                    if update_response.status_code == 200:
                        print("✅ Successfully updated record with lookup data!")
                        
                        # Verify the update
                        updated_record = self.get_record(record_id, layout_name)
                        if updated_record:
                            final_fields = updated_record.get('fieldData', {})
                            print("\n📋 Final Record State:")
                            print(f"  Part Number: {final_fields.get('PART NUMBER', 'EMPTY')}")
                            print(f"  Description: {final_fields.get('Description', 'EMPTY')}")
                            print(f"  Revision: {final_fields.get('Revision', 'EMPTY')}")
                            print(f"  Op Sheet Issue: {final_fields.get('Op Sheet Issue', 'EMPTY')}")
                            
                            if final_fields.get('Description') and final_fields.get('Revision'):
                                print("🎉 SUCCESS: Lookup simulation completed successfully!")
                                return True
                            else:
                                print("⚠️ WARNING: Fields updated but values appear empty")
                                return False
                        else:
                            print("Could not verify the update")
                            return True  # Assume success
                    else:
                        print(f"❌ Failed to update record with lookup data: {update_response.status_code} - {update_response.text}")
                        return False
                        
                else:
                    print(f"❌ No matching record found in PRICES table for Part Number: {part_number}")
                    print("   This means the part number doesn't exist in the PRICES table")
                    return False
                    
            elif find_response.status_code == 401:
                print("❌ No records found or access denied to PRICES table")
                print("   Check if the PRICES layout exists and is accessible")
                return False
            else:
                print(f"❌ Failed to search PRICES table: {find_response.status_code} - {find_response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Error simulating lookups via related data: {e}")
            import traceback
            traceback.print_exc()
            return False

    def run_script_on_record(self, record_id, script_name, script_params=None, layout_name="Time Clock"):
        """Run a FileMaker script on a specific record with optional parameters"""
        if not self.token:
            return False
        
        try:
            # Use PATCH on specific record to run script (correct approach)
            record_url = f"{self.server_url}/fmi/data/v1/databases/{self.database}/layouts/{layout_name}/records/{record_id}"
            
            payload = {
                "fieldData": {},  # Empty fieldData required for API
                "script": script_name
            }
            
            # Only add script parameter if provided
            if script_params:
                payload["script.param"] = script_params
            
            print(f"Executing script '{script_name}' on record {record_id} with params: {script_params}")
            
            response = requests.patch(record_url, json=payload, headers=self.get_headers(), verify=self.ssl_verify, timeout=self.timeout)
            
            if response.status_code == 200:
                result_data = response.json()
                script_result = result_data.get('response', {}).get('scriptResult', '')
                script_error = result_data.get('response', {}).get('scriptError', '')
                
                print(f"Script '{script_name}' executed successfully on record {record_id}")
                print(f"Script result: {script_result}")
                
                if script_error and script_error != "0":
                    print(f"Script error: {script_error}")
                    return False
                
                return script_result if script_result else True  # Return True if successful but no specific result
            else:
                print(f"Failed to execute script: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"Script execution error: {e}")
            import traceback
            traceback.print_exc()
            return False

    def get_record(self, record_id, layout_name="PreInventory"):
        """Get a specific record by ID"""
        if not self.token:
            return None
        
        try:
            get_url = f"{self.server_url}/fmi/data/v1/databases/{self.database}/layouts/{layout_name}/records/{record_id}"
            
            response = requests.get(get_url, headers=self.get_headers(), verify=self.ssl_verify, timeout=self.timeout)
            
            if response.status_code == 200:
                data = response.json()
                return data.get('response', {}).get('data', [{}])[0]
            else:
                print(f"Failed to get record {record_id}: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"Error getting record {record_id}: {e}")
            return None

    def get_all_records(self, layout_name="PreInventory", limit=10):
        """Get all records from a layout (with optional limit)"""
        if not self.token:
            return []
        
        try:
            get_url = f"{self.server_url}/fmi/data/v1/databases/{self.database}/layouts/{layout_name}/records"
            params = {"_limit": limit} if limit else {}
            
            response = requests.get(
                get_url, 
                headers=self.get_headers(), 
                params=params,
                verify=self.ssl_verify, 
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                records = result.get('response', {}).get('data', [])
                print(f"Found {len(records)} records")
                return records
            else:
                print(f"Failed to get records: {response.status_code} - {response.text}")
                return []
        except Exception as e:
            print(f"Error getting records: {e}")
            return []

    def find_existing_record(self, po_number, layout_name="PreInventory"):
        """Find an existing record by PO number"""
        if not self.token:
            return None
        
        try:
            find_url = f"{self.server_url}/fmi/data/v1/databases/{self.database}/layouts/{layout_name}/_find"
            find_payload = {
                "query": [
                    {
                        "Whittaker Shipper #": po_number
                    }
                ]
            }
            
            response = requests.post(
                find_url, 
                json=find_payload, 
                headers=self.get_headers(), 
                verify=self.ssl_verify, 
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                records = result.get('response', {}).get('data', [])
                if records:
                    record_id = records[0].get('recordId')
                    print(f"Found existing PO {po_number} with record ID: {record_id}")
                    return record_id
            
            print(f"No existing record found for PO {po_number}")
            return None
            
        except Exception as e:
            print(f"Error finding existing record for PO {po_number}: {e}")
            return None

    def update_existing_record(self, record_id, field_data, layout_name="PreInventory"):
        """Update an existing record with new data"""
        if not self.token:
            return False
        
        try:
            update_url = f"{self.server_url}/fmi/data/v1/databases/{self.database}/layouts/{layout_name}/records/{record_id}"
            
            # Only update fields that have new/different values
            update_fields = {}
            for field_name, value in field_data.items():
                if value is not None and str(value).strip():
                    update_fields[field_name] = str(value).strip()
            
            if not update_fields:
                print("No fields to update")
                return True
            
            payload = {"fieldData": update_fields}
            
            response = requests.patch(
                update_url, 
                json=payload, 
                headers=self.get_headers(), 
                verify=self.ssl_verify, 
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                print(f"Successfully updated record {record_id}")
                return True
            else:
                print(f"Failed to update record {record_id}: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"Error updating record {record_id}: {e}")
            return False

    def backup_relookup_method(self, record_id, field_data, layout_name, config):
        """Backup method to force relookup using field updates - specifically for Part Number lookups"""
        if not self.token:
            return False
        
        try:
            print(f"Using backup relookup method for record {record_id}")
            
            update_url = f"{self.server_url}/fmi/data/v1/databases/{self.database}/layouts/{layout_name}/records/{record_id}"
            
            # Method 1: Update the Part Number field to trigger Description, Revision, Op Sheet Issue lookups
            part_number = field_data.get('PART NUMBER', '')
            if part_number:
                payload = {
                    "fieldData": {
                        "PART NUMBER": part_number
                    }
                }
                
                print(f"Triggering part number lookups by updating: PART NUMBER = {part_number}")
                response = requests.patch(update_url, json=payload, headers=self.get_headers(), verify=self.ssl_verify, timeout=self.timeout)
                
                if response.status_code == 200:
                    print(f"Part number lookup trigger successful for record {record_id}")
                else:
                    print(f"Part number lookup trigger failed: {response.status_code} - {response.text}")
                
                # Wait a moment for FileMaker to process the lookup
                import time
                time.sleep(1)
            
            # Method 2: Also update Planner Name field if it exists (from the buyer lookup)
            planner_name = field_data.get('Planner Name', '')
            if planner_name:
                payload = {
                    "fieldData": {
                        "Planner Name": planner_name
                    }
                }
                
                print(f"Triggering planner lookup by updating: Planner Name = {planner_name}")
                response = requests.patch(update_url, json=payload, headers=self.get_headers(), verify=self.ssl_verify, timeout=self.timeout)
                
                if response.status_code == 200:
                    print(f"Planner name lookup trigger successful for record {record_id}")
                else:
                    print(f"Planner name lookup trigger failed: {response.status_code} - {response.text}")
            
            # Method 3: Update PO number last to trigger any PO-based lookups
            po_number = field_data.get('Whittaker Shipper #', '')
            if po_number:
                payload = {
                    "fieldData": {
                        "Whittaker Shipper #": po_number
                    }
                }
                
                print(f"Triggering PO lookups by updating: Whittaker Shipper # = {po_number}")
                response = requests.patch(update_url, json=payload, headers=self.get_headers(), verify=self.ssl_verify, timeout=self.timeout)
                
                if response.status_code == 200:
                    print(f"PO number lookup trigger successful for record {record_id}")
                else:
                    print(f"PO number lookup trigger failed: {response.status_code} - {response.text}")
            
            return True
                        
        except Exception as e:
            print(f"Error in backup relookup method: {e}")
            return False

    def trigger_lookups(self, record_id, field_data, layout_name="PreInventory", lookup_fields=None):
        """Trigger FileMaker lookups by updating specific fields"""
        if not self.token:
            return False
        
        try:
            update_url = f"{self.server_url}/fmi/data/v1/databases/{self.database}/layouts/{layout_name}/records/{record_id}"
            
            # If specific lookup fields are provided, update only those
            if lookup_fields:
                update_data = {field: field_data.get(field, '') for field in lookup_fields if field in field_data}
            else:
                # Otherwise, update all fields to trigger all lookups
                update_data = field_data
            
            payload = {
                "fieldData": update_data
            }
            
            response = requests.patch(update_url, json=payload, headers=self.get_headers(), verify=self.ssl_verify, timeout=self.timeout)
            
            if response.status_code == 200:
                print(f"Lookups triggered for record {record_id}")
                return True
            else:
                print(f"Failed to trigger lookups: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"Error triggering lookups: {e}")
            return False
    
    def create_filemaker_record(self, po_data, layout_name="PO_Processing"):
        """Create a record in FileMaker"""
        if not self.token:
            if not self.authenticate():
                return False
        
        try:
            create_url = f"{self.server_url}/fmi/data/v1/databases/{self.database}/layouts/{layout_name}/records"
            
            # Map PO data to FileMaker fields
            field_data = self.map_to_filemaker_fields(po_data)
            
            payload = {
                "fieldData": field_data
            }
            
            response = requests.post(create_url, json=payload, headers=self.get_headers())
            
            if response.status_code == 200:
                result = response.json()
                return result.get('response', {}).get('recordId')
            else:
                print(f"Failed to create record: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"Error creating FileMaker record: {e}")
            return False
    
    def map_to_filemaker_fields(self, po_data):
        """Map PO data to FileMaker field structure"""
        # This mapping will depend on your specific FileMaker database schema
        # Adjust field names to match your FileMaker layout
        
        field_data = {
            "PO_Number": po_data.get("po_folder", ""),
            "Processing_Date": po_data.get("timestamp", ""),
            "JSON_Data": json.dumps(po_data.get("extracted_data", {})),
            "PDF_Count": len(po_data.get("files", {}).get("pdf_files", [])),
            "JSON_Count": len(po_data.get("files", {}).get("json_files", [])),
            "Status": "Processed",
            "Source_System": "Parker_PO_OCR"
        }
        
        # Extract specific PO details if available
        extracted_data = po_data.get("extracted_data", {})
        
        # Look for common PO information in extracted data
        for data_source, data in extracted_data.items():
            if isinstance(data, dict):
                # Map common fields
                if "po_number" in data:
                    field_data["PO_Number"] = data["po_number"]
                if "vendor" in data:
                    field_data["Vendor"] = data["vendor"]
                if "total_amount" in data:
                    field_data["Total_Amount"] = data["total_amount"]
                if "date" in data:
                    field_data["PO_Date"] = data["date"]
                if "items" in data and isinstance(data["items"], list):
                    field_data["Item_Count"] = len(data["items"])
                    field_data["Items_JSON"] = json.dumps(data["items"])
        
        return field_data
    
    def export_for_filemaker(self, po_folders=None):
        """Export all or specific PO folders for FileMaker import"""
        if po_folders is None:
            # Get all PO folders
            pos_path = os.path.join(self.base_path, "POs")
            po_folders = [d for d in os.listdir(pos_path) 
                         if os.path.isdir(os.path.join(pos_path, d)) and d.startswith('455')]
        
        export_data = {
            "export_timestamp": datetime.now().isoformat(),
            "total_pos": len(po_folders),
            "pos": []
        }
        
        for po_folder in po_folders:
            po_folder_path = os.path.join(self.base_path, "POs", po_folder)
            po_data = self.prepare_po_data(po_folder_path)
            export_data["pos"].append(po_data)
        
        return export_data
    
    def save_export_file(self, export_data, filename=None):
        """Save export data to JSON file"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"filemaker_export_{timestamp}.json"
        
        export_path = os.path.join(self.base_path, "dashboard", filename)
        
        try:
            with open(export_path, 'w') as f:
                json.dump(export_data, f, indent=2)
            return export_path
        except Exception as e:
            print(f"Error saving export file: {e}")
            return None

    def export_record_as_pdf(self, record_id, layout_name="Time Clock", output_path=None):
        """
        Export a FileMaker record as PDF using script method
        This method is optimized for Time Clock layout with barcodes
        """
        if not self.token:
            print("No authentication token available")
            return False
        
        try:
            print(f"📄 Exporting record {record_id} as PDF using Time Clock layout with PDFTimesheet script")
            
            # For Time Clock layout with barcodes, use script-based export directly
            # since Data API doesn't handle barcode rendering well
            return self.export_via_script(record_id, layout_name, output_path)
                
        except Exception as e:
            print(f"❌ Error exporting PDF: {e}")
            import traceback
            traceback.print_exc()
            return False

    def export_via_script(self, record_id, layout_name, output_path=None):
        """
        Export PDF using FileMaker script that requires no parameters
        The script automatically saves PDF to server's Documents folder
        """
        try:
            print(f"📝 Using FileMaker script for PDF export (no parameters needed)...")
            
            # Execute PDF export script without parameters
            script_result = self.run_script_on_record(
                record_id, 
                "PDFTimesheet",  # Your custom PDF export script
                None,  # No parameters needed
                layout_name
            )
            
            
            if script_result:
                print(f"✅ PDF export script completed")
                # Parse the script result to get the actual file path
                if isinstance(script_result, str) and ("SUCCESS:" in script_result or "file:" in script_result):
                    # Extract file path from script result
                    if "SUCCESS:" in script_result:
                        file_path = script_result.replace("SUCCESS:", "").strip()
                    else:
                        file_path = script_result.strip()
                    print(f"📄 PDF saved to: {file_path}")
                    return file_path
                else:
                    print(f"📄 PDF export completed, result: {script_result}")
                    # Return a generic success indicator since no path provided
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    return f"PDF_export_{record_id}_{timestamp}.pdf"
            else:
                print(f"❌ PDF export script failed")
                return False
                
        except Exception as e:
            print(f"❌ Error in script-based export: {e}")
            return False

    def get_record_for_export(self, record_id, layout_name="Time Clock"):
        """Get record data formatted for export/printing"""
        if not self.token:
            return None
        
        try:
            record = self.get_record(record_id, layout_name)
            
            if record:
                field_data = record.get('fieldData', {})
                
                # Format data for export
                export_data = {
                    'record_id': record_id,
                    'po_number': field_data.get('Whittaker Shipper #', ''),
                    'part_number': field_data.get('PART NUMBER', ''),
                    'part_name': field_data.get('Part Name', ''),
                    'quantity': field_data.get('QTY SHIP', ''),
                    'mjo_number': field_data.get('MJO NO', ''),
                    'delivery_date': field_data.get('Promise Delivery Date', ''),
                    'planner_name': field_data.get('Planner Name', ''),
                    'revision': field_data.get('Revision', ''),
                    'op_sheet_issue': field_data.get('Op Sheet Issue', ''),
                    'date_in': field_data.get('Date In', ''),
                    'assembly_notes': field_data.get('PRICES 7-9-2002.fp7::Assembly Notes', '')
                }
                
                return export_data
            else:
                return None
                
        except Exception as e:
            print(f"Error getting record for export: {e}")
            return None

# Example usage and configuration
def create_sample_config():
    """Create a sample configuration for FileMaker integration"""
    config = {
        "filemaker": {
            "server_url": "https://your-filemaker-server.com",
            "database": "PO_Management",
            "username": "api_user",
            "password": "secure_password",
            "layout_name": "PO_Processing"
        },
        "field_mapping": {
            "PO_Number": "po_number",
            "Vendor": "vendor",
            "Total_Amount": "total_amount",
            "PO_Date": "date",
            "Status": "Processed",
            "Source_System": "Parker_PO_OCR"
        },
        "auto_sync": False,
        "sync_interval_minutes": 60
    }
    
    config_path = "/volume1/Main/Main/ParkerPOsOCR/dashboard/filemaker_config.json"
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)
    
    return config_path

if __name__ == "__main__":
    # Create sample configuration
    config_file = create_sample_config()
    print(f"Sample FileMaker configuration created: {config_file}")
    
    # Example of preparing export data
    fm = FileMakerIntegration(
        server_url="https://your-filemaker-server.com",
        database="PO_Management", 
        username="api_user",
        password="secure_password"
    )
    
    export_data = fm.export_for_filemaker()
    export_file = fm.save_export_file(export_data)
    
    if export_file:
        print(f"Export file created: {export_file}")
        print(f"Records exported: {export_data['total_pos']}")
    else:
        print("Failed to create export file")
