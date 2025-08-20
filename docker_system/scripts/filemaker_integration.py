"""
FileMaker Data API Integration for PO Processing
Phase 1b - To be used after container testing is complete
"""

import json
import os
import requests
import urllib3

# Suppress SSL certificate warnings for self-signed certificates
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class FileMakerIntegration:
    def __init__(self):
        self.server = os.getenv('FILEMAKER_SERVER', 'https://192.168.0.105:443')
        self.database = os.getenv('FILEMAKER_DATABASE', 'PreInventory')
        self.layout = os.getenv('FILEMAKER_LAYOUT', 'PreInventory')
        # Script to run on create/patch and target print layout are now configurable
        self.script_name = os.getenv('FILEMAKER_SCRIPT', 'PDFTimesheet')
        # This is the layout the FileMaker script should switch to before saving as PDF
        # Your FileMaker script should read this from Get(ScriptParameter) and use
        # Go to Layout [ Layout Name by Calculation: $layout ]
        self.print_layout = os.getenv('FILEMAKER_PRINT_LAYOUT', 'Time Clock Reduced')
        self.username = os.getenv('FILEMAKER_USERNAME', 'JSON')
        self.password = os.getenv('FILEMAKER_PASSWORD', 'Windu63Purple!')
        self.token = None
        # Telemetry for last operation
        self.last_status_code = None
        self.last_response_text = None
        self.last_error = None
        self.last_script_error = None
        self.last_script_result = None
        self.last_record_id = None

        # Allowed FileMaker Planner Name values
        self.allowed_planners = [
            "Steven Huynh",
            "Lisa Munoz",
            "Frank Davis",
            "William Estrada",
            "Glenn Castellon",
            "Sean Klesert",
            "Michael Reyes",
            "Nataly Hernandez",
            "Robert Lopez",
            "Daniel Rodriguez",
            "Diana Betancourt",
            "Diane Crone",
            "Amy Schlock",
            "Cesar Sarabia",
            "Anthony Frederick",
            "Nora Seclen",
        ]

    def _normalize_name(self, name: str):
        if not name:
            return None
        return ' '.join(str(name).split())

    def _map_planner(self, buyer_name: str) -> str:
        cleaned = self._normalize_name(buyer_name) or ""
        for val in self.allowed_planners:
            if cleaned.lower() == val.lower():
                return val
        parts = cleaned.split()
        if len(parts) >= 2:
            last = parts[-1].lower()
            candidates = [v for v in self.allowed_planners if v.split()[-1].lower() == last]
            if len(candidates) == 1:
                return candidates[0]
        return "Steven Huynh"

    def authenticate(self):
        """Authenticate with FileMaker Data API"""
        url = f"{self.server}/fmi/data/v1/databases/{self.database}/sessions"
        import base64
        credentials = f"{self.username}:{self.password}"
        encoded_credentials = base64.b64encode(credentials.encode('utf-8')).decode('utf-8')
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Basic {encoded_credentials}'
        }
        try:
            response = requests.post(url, json={}, headers=headers, verify=False)
            self.last_status_code = response.status_code
            self.last_response_text = response.text
            if response.status_code == 200:
                self.token = response.json()['response']['token']
                print("✅ FileMaker authentication successful")
                return True
            else:
                print(f"❌ FileMaker authentication failed: {response.status_code}")
                print(f"Response: {response.text}")
                self.last_error = f"Auth failed: {response.status_code}"
                return False
        except Exception as e:
            print(f"❌ FileMaker connection error: {e}")
            self.last_error = f"Connection error: {e}"
            return False

    def insert_po_data(self, po_info):
        """Insert PO data into FileMaker database and trigger PDFTimesheet script"""
        if not self.token:
            if not self.authenticate():
                return False
        # reset telemetry
        self.last_status_code = None
        self.last_response_text = None
        self.last_error = None
        self.last_script_error = None
        self.last_script_result = None
        self.last_record_id = None

        planner_name = self._map_planner(po_info.get("buyer_name"))
        
        # Format DPAS ratings for FileMaker value list
        dpas_ratings_raw = po_info.get("dpas_ratings", [])
        dpas_ratings_formatted = ""
        if dpas_ratings_raw and isinstance(dpas_ratings_raw, list):
            # Convert to comma-separated string for FileMaker value list
            dpas_ratings_formatted = ", ".join(dpas_ratings_raw)
        
        # Format Q clause analysis for FileMaker (following recommended Option 2 structure)
        quality_clauses_analysis = po_info.get("quality_clauses_analysis", {})
        q_clauses_accept = ""
        q_clauses_review = ""
        q_clauses_object = ""
        q_status = "Not Reviewed"
        timesheet_impact = "No"
        
        if quality_clauses_analysis:
            # Extract classified clauses
            classified = quality_clauses_analysis.get("classified_clauses", {})
            
            # Auto-accept clauses (standard compliance)
            auto_accept = classified.get("auto_accept", [])
            if auto_accept:
                q_clauses_accept = ", ".join([c.get("clause_id", "") for c in auto_accept if c.get("clause_id")])
            
            # Review required clauses (timesheet impact)
            review_required = classified.get("review_required", [])
            if review_required:
                q_clauses_review = ", ".join([c.get("clause_id", "") for c in review_required if c.get("clause_id")])
                timesheet_impact = "Yes"  # Any review required clauses indicate timesheet impact
            
            # Object to clauses (non-compliance)
            object_to = classified.get("object_to", [])
            if object_to:
                q_clauses_object = ", ".join([c.get("clause_id", "") for c in object_to if c.get("clause_id")])
            
            # Overall status based on classification
            total_clauses = len(auto_accept) + len(review_required) + len(object_to)
            if total_clauses > 0:
                if object_to:
                    q_status = "Objection Required"
                elif review_required:
                    q_status = "Review Required"
                else:
                    q_status = "Auto Accept"
        
        preinventory_data = {
            "fieldData": {
                "Whittaker Shipper #": str(po_info.get("purchase_order_number", "")),
                "MJO NO": str(po_info.get("production_order", "")),
                "PART NUMBER": str(po_info.get("part_number", "")),
                "QTY SHIP": int(po_info.get("quantity", 0)) if po_info.get("quantity") else 0,
                "Revision": str(po_info.get("revision", "")),
                "Planner Name": planner_name,
                # Map dock_date to Promise Delivery Date in FileMaker (layout field name)
                "Promise Delivery Date": str(po_info.get("dock_date", "")) if po_info.get("dock_date") else "",
                # Map DPAS ratings to FileMaker value list field
                "DPAS Rating": dpas_ratings_formatted,
                # Q Clause fields will be added when FileMaker layout is updated
                # "Q_Clauses_Accept": q_clauses_accept,
                # "Q_Clauses_Review": q_clauses_review,
                # "Q_Clauses_Object": q_clauses_object,
                # "Q_Clauses_Status": q_status,
                # "Q_Timesheet_Impact": timesheet_impact,
            }
        }

        headers = {
            'Authorization': f'Bearer {self.token}',
            'Content-Type': 'application/json'
        }
        preinventory_url = f"{self.server}/fmi/data/v1/databases/{self.database}/layouts/{self.layout}/records"

        try:
            po_number = po_info.get('purchase_order_number', 'Unknown')
            # Pass JSON parameter so the FileMaker script can choose the print layout dynamically
            script_param = json.dumps({
                "po": str(po_number),
                "layout": self.print_layout
            })
            print(f"➡️  Triggering FileMaker script '{self.script_name}' with layout '{self.print_layout}' for PO {po_number}")
            preinventory_data_with_script = {
                "fieldData": preinventory_data["fieldData"],
                "script": self.script_name,
                "script.param": script_param
            }

            preinventory_response = requests.post(preinventory_url, json=preinventory_data_with_script, headers=headers, verify=False)
            self.last_status_code = preinventory_response.status_code
            self.last_response_text = preinventory_response.text

            if preinventory_response.status_code == 500 and '"code":"506"' in preinventory_response.text:
                print("⚠️ Validation error 506 - retrying with safe fallback values for value-list fields")
                safe_fields = dict(preinventory_data_with_script["fieldData"])
                safe_fields["Planner Name"] = self._map_planner(po_info.get("buyer_name")) or "Steven Huynh"
                if "PART NUMBER" in safe_fields:
                    safe_fields["PART NUMBER"] = str(safe_fields["PART NUMBER"]) or "UNKNOWN"
                if "MJO NO" in safe_fields:
                    safe_fields["MJO NO"] = str(safe_fields["MJO NO"]) or ""
                retry_body = {"fieldData": safe_fields}
                retry_resp = requests.post(preinventory_url, json=retry_body, headers=headers, verify=False)
                self.last_status_code = retry_resp.status_code
                self.last_response_text = retry_resp.text
                if retry_resp.status_code == 200:
                    print("✅ PreInventory insert succeeded on retry (without script). Triggering script separately...")
                    record_id = retry_resp.json().get('response', {}).get('recordId')
                    self.last_record_id = record_id
                    if record_id:
                        edit_url = f"{preinventory_url}/{record_id}"
                        print(f"➡️  Triggering FileMaker script '{self.script_name}' (edit) with layout '{self.print_layout}' for PO {po_number}")
                        edit_body = {"fieldData": {}, "script": self.script_name, "script.param": script_param}
                        script_resp = requests.patch(edit_url, json=edit_body, headers=headers, verify=False)
                        try:
                            resp_json = script_resp.json().get('response', {}) if script_resp.status_code == 200 else {}
                            self.last_script_error = resp_json.get('scriptError')
                            self.last_script_result = resp_json.get('scriptResult')
                        except Exception:
                            pass
                        if script_resp.status_code == 200:
                            print("✅ PDFTimesheet script executed on existing record")
                        else:
                            print(f"⚠️ Script execution via edit failed: {script_resp.status_code} - {script_resp.text}")
                    return True
                else:
                    print(f"⚠️ Retry insert failed: {retry_resp.status_code} - {retry_resp.text}")
                    self.last_error = f"Retry insert failed: {retry_resp.status_code}"
                    return False

            # Handle FileMaker error 102 (field missing) by progressively retrying with known-safe field sets
            if preinventory_response.status_code == 500 and '"code":"102"' in preinventory_response.text:
                print("⚠️ Field missing (102) - progressively retrying with safer field sets")

                def try_insert_and_trigger(fields: dict):
                    body = {"fieldData": fields}
                    resp = requests.post(preinventory_url, json=body, headers=headers, verify=False)
                    self.last_status_code = resp.status_code
                    self.last_response_text = resp.text
                    if resp.status_code == 200:
                        print("✅ PreInventory insert succeeded (safe 102-retry). Updating fields and triggering script...")
                        record_id = resp.json().get('response', {}).get('recordId')
                        self.last_record_id = record_id
                        if record_id:
                            edit_url = f"{preinventory_url}/{record_id}"
                            po_number_local = po_info.get('purchase_order_number', 'Unknown')
                            # Prepare full non-container field update aligned with layout
                            planner_name_local = self._map_planner(po_info.get("buyer_name"))
                            
                            # Format DPAS ratings for FileMaker value list (in safe retry)
                            dpas_ratings_raw_local = po_info.get("dpas_ratings", [])
                            dpas_ratings_formatted_local = ""
                            if dpas_ratings_raw_local and isinstance(dpas_ratings_raw_local, list):
                                # Convert to comma-separated string for FileMaker value list
                                dpas_ratings_formatted_local = ", ".join(dpas_ratings_raw_local)
                            
                            # Format Q clause analysis for FileMaker (safe retry)
                            quality_clauses_analysis_local = po_info.get("quality_clauses_analysis", {})
                            q_clauses_accept_local = ""
                            q_clauses_review_local = ""
                            q_clauses_object_local = ""
                            q_status_local = "Not Reviewed"
                            timesheet_impact_local = "No"
                            
                            if quality_clauses_analysis_local:
                                # Extract classified clauses
                                classified_local = quality_clauses_analysis_local.get("classified_clauses", {})
                                
                                # Auto-accept clauses (standard compliance)
                                auto_accept_local = classified_local.get("auto_accept", [])
                                if auto_accept_local:
                                    q_clauses_accept_local = ", ".join([c.get("clause_id", "") for c in auto_accept_local if c.get("clause_id")])
                                
                                # Review required clauses (timesheet impact)
                                review_required_local = classified_local.get("review_required", [])
                                if review_required_local:
                                    q_clauses_review_local = ", ".join([c.get("clause_id", "") for c in review_required_local if c.get("clause_id")])
                                    timesheet_impact_local = "Yes"  # Any review required clauses indicate timesheet impact
                                
                                # Object to clauses (non-compliance)
                                object_to_local = classified_local.get("object_to", [])
                                if object_to_local:
                                    q_clauses_object_local = ", ".join([c.get("clause_id", "") for c in object_to_local if c.get("clause_id")])
                                
                                # Overall status based on classification
                                total_clauses_local = len(auto_accept_local) + len(review_required_local) + len(object_to_local)
                                if total_clauses_local > 0:
                                    if object_to_local:
                                        q_status_local = "Objection Required"
                                    elif review_required_local:
                                        q_status_local = "Review Required"
                                    else:
                                        q_status_local = "Auto Accept"
                            
                            update_fields = {
                                "Whittaker Shipper #": str(po_info.get("purchase_order_number", "")),
                                "MJO NO": str(po_info.get("production_order", "")),
                                "PART NUMBER": str(po_info.get("part_number", "")),
                                "QTY SHIP": int(po_info.get("quantity", 0)) if po_info.get("quantity") else 0,
                                "Revision": str(po_info.get("revision", "")),
                                "Planner Name": planner_name_local or "Steven Huynh",
                                "Promise Delivery Date": str(po_info.get("dock_date", "")) if po_info.get("dock_date") else "",
                                # Include DPAS Rating in safe retry
                                "DPAS Rating": dpas_ratings_formatted_local,
                                # Q Clause fields will be added when FileMaker layout is updated
                                # "Q_Clauses_Accept": q_clauses_accept_local,
                                # "Q_Clauses_Review": q_clauses_review_local,
                                # "Q_Clauses_Object": q_clauses_object_local,
                                # "Q_Clauses_Status": q_status_local,
                                # "Q_Timesheet_Impact": timesheet_impact_local,
                            }
                            # First update fields
                            upd_resp = requests.patch(edit_url, json={"fieldData": update_fields}, headers=headers, verify=False)
                            if upd_resp.status_code != 200:
                                print(f"⚠️ Field update after safe insert failed: {upd_resp.status_code} - {upd_resp.text}")
                            # Then trigger the script
                            # Trigger script after updating fields; pass JSON param with layout
                            script_param_local = json.dumps({"po": str(po_number_local), "layout": self.print_layout})
                            print(f"➡️  Triggering FileMaker script '{self.script_name}' (102 path) with layout '{self.print_layout}' for PO {po_number_local}")
                            edit_body = {"fieldData": {}, "script": self.script_name, "script.param": script_param_local}
                            script_resp = requests.patch(edit_url, json=edit_body, headers=headers, verify=False)
                            try:
                                resp_json = script_resp.json().get('response', {}) if script_resp.status_code == 200 else {}
                                self.last_script_error = resp_json.get('scriptError')
                                self.last_script_result = resp_json.get('scriptResult')
                            except Exception:
                                pass
                            if script_resp.status_code == 200:
                                print("✅ PDFTimesheet script executed on existing record (102-safe path)")
                            else:
                                print(f"⚠️ Script execution via edit failed: {script_resp.status_code} - {script_resp.text}")
                        return True
                    else:
                        print(f"⚠️ Safe insert attempt failed: {resp.status_code} - {resp.text}")
                        return False

                po_num = str(po_info.get("purchase_order_number", ""))
                # Use non-container numeric field as primary safe key
                safe_field_sets = [
                    {"Whittaker Shipper #": po_num},
                    # If needed, try adding minimal other known-good fields
                    {"Whittaker Shipper #": po_num, "QTY SHIP": int(po_info.get("quantity", 0)) if po_info.get("quantity") else 0},
                    # As last resort, include container keys though we don't upload content here
                    {"Whittaker Shipper #": po_num, "IncomingPO": po_num},
                ]

                for fields in safe_field_sets:
                    if try_insert_and_trigger(fields):
                        return True

                # If all safe attempts failed, record error and bail out
                self.last_error = "Retry insert (102) failed with all safe field sets"
                return False

            if preinventory_response.status_code == 200:
                response_data = preinventory_response.json().get('response', {})
                preinventory_record_id = response_data.get('recordId')
                script_error = response_data.get('scriptError', '0')
                script_result = response_data.get('scriptResult', 'No result')
                self.last_record_id = preinventory_record_id
                self.last_script_error = script_error
                self.last_script_result = script_result

                print(f"✅ PO {po_info.get('purchase_order_number')} inserted to PreInventory (Record ID: {preinventory_record_id})")
                if script_error == '0':
                    print("✅ PDFTimesheet script executed successfully during PreInventory record creation")
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
                print(f"⚠️ PreInventory insert (with script) failed: {preinventory_response.status_code}")
                try:
                    print(f"Response: {preinventory_response.text}")
                except Exception:
                    pass
                self.last_error = f"Insert failed: {preinventory_response.status_code}"
                return False
        except Exception as e:
            print(f"❌ FileMaker insert error: {e}")
            self.last_error = f"Insert exception: {e}"
            return False

    def _log_script_error(self, error_code):
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
        import subprocess
        import time
        pdf_path = f"/Users/Shared/ParkerPOsOCR/exports/{po_number}.pdf"
        mac_host = "192.168.0.105"
        ssh_user = "Anthony"
        time.sleep(2)
        try:
            ssh_command = f'ssh {ssh_user}@{mac_host} "lp \"{pdf_path}\""'
            print(f"🖨️ Sending PDF to printer: {pdf_path}")
            result = subprocess.run(ssh_command, shell=True, capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                print("✅ PDF sent to default printer successfully")
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
        expected_path = f"/Users/Shared/ParkerPOsOCR/exports/{po_number}.pdf"
        print("💡 To verify PDF generation, check Mac FileMaker Server at:")
        print(f"   📁 {expected_path}")
        print("   🔧 You can also check via FileMaker Server Admin Console or SSH to server")

    def check_duplicate_po(self, po_number):
        if not self.token:
            if not self.authenticate():
                return False
        url = f"{self.server}/fmi/data/v1/databases/{self.database}/layouts/{self.layout}/_find"
        # Use non-container numeric field for find
        find_request = {"query": [{"Whittaker Shipper #": str(po_number)}]}
        headers = {'Authorization': f'Bearer {self.token}', 'Content-Type': 'application/json'}
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

    def update_existing_record(self, po_info):
        """Update fields on an existing record identified by Whittaker Shipper #."""
        if not self.token:
            if not self.authenticate():
                return False
        po_num = str(po_info.get("purchase_order_number", ""))
        # find recordId by Whittaker Shipper #
        find_url = f"{self.server}/fmi/data/v1/databases/{self.database}/layouts/{self.layout}/_find"
        headers = {'Authorization': f'Bearer {self.token}', 'Content-Type': 'application/json'}
        try:
            resp = requests.post(find_url, json={"query": [{"Whittaker Shipper #": po_num}]}, headers=headers, verify=False)
            if resp.status_code != 200:
                print(f"⚠️ Update find failed: {resp.status_code} - {resp.text}")
                return False
            data = resp.json().get('response', {}).get('data', [])
            if not data:
                print("⚠️ No existing record found to update")
                return False
            record_id = data[0].get('recordId')
            if not record_id:
                print("⚠️ No recordId in find response")
                return False
            # Prepare update fields aligned with layout
            planner_name = self._map_planner(po_info.get("buyer_name"))
            update_fields = {
                "MJO NO": str(po_info.get("production_order", "")),
                "PART NUMBER": str(po_info.get("part_number", "")),
                "QTY SHIP": int(po_info.get("quantity", 0)) if po_info.get("quantity") else 0,
                "Revision": str(po_info.get("revision", "")),
                "Planner Name": planner_name,
                "Promise Delivery Date": str(po_info.get("dock_date", "")) if po_info.get("dock_date") else "",
            }
            edit_url = f"{self.server}/fmi/data/v1/databases/{self.database}/layouts/{self.layout}/records/{record_id}"
            edit_body = {"fieldData": update_fields}
            edit_resp = requests.patch(edit_url, json=edit_body, headers=headers, verify=False)
            self.last_status_code = edit_resp.status_code
            self.last_response_text = edit_resp.text
            if edit_resp.status_code == 200:
                print(f"✅ Updated existing record {record_id} for PO {po_num}")
                return True
            else:
                print(f"⚠️ Update failed: {edit_resp.status_code} - {edit_resp.text}")
                return False
        except Exception as e:
            print(f"❌ Update exception: {e}")
            return False

    def update_record_by_id(self, record_id: str, po_info):
        """Update fields on a specific record by recordId (best-effort alignment to layout)."""
        if not self.token:
            if not self.authenticate():
                return False
        headers = {'Authorization': f'Bearer {self.token}', 'Content-Type': 'application/json'}
        # Prepare update fields aligned with layout (no containers)
        planner_name = self._map_planner(po_info.get("buyer_name"))
        update_fields = {
            "Whittaker Shipper #": str(po_info.get("purchase_order_number", "")),
            "MJO NO": str(po_info.get("production_order", "")),
            "PART NUMBER": str(po_info.get("part_number", "")),
            "QTY SHIP": int(po_info.get("quantity", 0)) if po_info.get("quantity") else 0,
            "Revision": str(po_info.get("revision", "")),
            "Planner Name": planner_name,
            "Promise Delivery Date": str(po_info.get("dock_date", "")) if po_info.get("dock_date") else "",
        }
        edit_url = f"{self.server}/fmi/data/v1/databases/{self.database}/layouts/{self.layout}/records/{record_id}"
        edit_body = {"fieldData": update_fields}
        try:
            edit_resp = requests.patch(edit_url, json=edit_body, headers=headers, verify=False)
            self.last_status_code = edit_resp.status_code
            self.last_response_text = edit_resp.text
            if edit_resp.status_code == 200:
                print(f"✅ Updated record {record_id} with PO data")
                return True
            else:
                print(f"⚠️ Update by id failed: {edit_resp.status_code} - {edit_resp.text}")
                return False
        except Exception as e:
            print(f"❌ Update by id exception: {e}")
            return False

    def logout(self):
        if self.token:
            url = f"{self.server}/fmi/data/v1/databases/{self.database}/sessions/{self.token}"
        
            try:
                requests.delete(url, verify=False)
                print("✅ FileMaker session closed")
            except Exception as e:
                print(f"❌ FileMaker disconnect error: {e}")

    def disconnect(self):
        self.logout()

    def list_layout_fields(self, layout: str = None):
        """Return FileMaker layout field metadata to diagnose 102 errors."""
        if not self.token:
            if not self.authenticate():
                return None
        layout_name = layout or self.layout
        url = f"{self.server}/fmi/data/v1/databases/{self.database}/layouts/{layout_name}"
        headers = {'Authorization': f'Bearer {self.token}', 'Content-Type': 'application/json'}
        try:
            resp = requests.get(url, headers=headers, verify=False)
            self.last_status_code = resp.status_code
            self.last_response_text = resp.text
            if resp.status_code == 200:
                data = resp.json().get('response', {})
                # Commonly under 'layout' -> 'fields'
                fields = (data.get('layout') or {}).get('fields') or []
                names = [f.get('name') for f in fields if isinstance(f, dict)]
                print(f"ℹ️ Fields on layout '{layout_name}':")
                for n in names:
                    print(f" - {n}")
                return names
            else:
                print(f"⚠️ Failed to fetch layout metadata: {resp.status_code} - {resp.text}")
                return None
        except Exception as e:
            print(f"❌ Layout metadata error: {e}")
            return None


def integrate_with_filemaker(po_folder_path):
    fm = FileMakerIntegration()
    json_file = os.path.join(po_folder_path, f"{os.path.basename(po_folder_path)}_info.json")
    if not os.path.exists(json_file):
        print(f"❌ JSON file not found: {json_file}")
        return False
    try:
        with open(json_file, 'r') as f:
            po_info = json.load(f)
        po_number = po_info.get("purchase_order_number")
        if fm.check_duplicate_po(po_number):
            print(f"⚠️  PO {po_number} already exists in FileMaker - skipping")
            return True
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
    fm = FileMakerIntegration()
    if fm.authenticate():
        print("FileMaker Data API connection test successful!")
        fm.disconnect()
    else:
        print("FileMaker Data API connection test failed!")