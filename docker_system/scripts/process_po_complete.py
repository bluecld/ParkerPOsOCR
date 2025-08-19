"""
Complete PO Processing Pipeline
- Converts PDF to searchable PDF with OCR
- Extracts all PO information to JSON
- Splits PDF into PO and Router sections  
- Organizes all files in PO-numbered folder
- Ready for folder monitoring automation
"""

import os
import sys
import subprocess
import json
import urllib3
from pathlib import Path
from datetime import datetime

# Suppress SSL certificate warnings for self-signed certificates
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
from filemaker_integration import FileMakerIntegration
import base64
import requests

def process_pdf_file(input_pdf_path):
    """Complete processing pipeline for a PDF file"""
    
    # Validate input file
    if not os.path.exists(input_pdf_path):
        print(f"Error: Input file '{input_pdf_path}' not found")
        return False
    
    print(f"Starting complete PO processing for: {input_pdf_path}")
    input_filename = os.path.basename(input_pdf_path)
    base_name = os.path.splitext(input_filename)[0]
    
    # Step 1: Create searchable PDF using OCR
    print("\\n=== Step 1: OCR Processing ===")
    searchable_pdf = f"{base_name}_searchable.pdf"
    
    try:
        result = subprocess.run([
            sys.executable, "ocr_pdf_searchable.py",
            input_pdf_path, searchable_pdf
        ], capture_output=True, text=True, check=True)
        print("OCR processing completed successfully")
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print("[OCR STDERR]", result.stderr)
    except subprocess.CalledProcessError as e:
        print(f"OCR processing failed: {e}")
        print("STDOUT:", e.stdout)
        print("STDERR:", e.stderr)
        # Write error details to error folder
        error_folder = os.getenv('ERROR_FOLDER', '/app/errors')
        error_file = os.path.join(error_folder, f"{base_name}_ocr_error.txt")
        with open(error_file, 'w') as ef:
            ef.write(f"OCR Error\nSTDOUT:\n{e.stdout}\n\nSTDERR:\n{e.stderr}\n")
        return False
    
    # Step 2: Extract PO information and split PDF
    print("\n=== Step 2: Information Extraction & PDF Splitting ===")
    env = os.environ.copy()
    env["SEARCHABLE_PDF"] = os.path.abspath(searchable_pdf)
    try:
        result = subprocess.run(
            [sys.executable, "extract_po_info.py"],
            capture_output=True,
            text=True,
            check=True,
            env=env,
        )
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print("[BASIC EXTRACT STDERR]", result.stderr)
        print("Basic PO extraction completed")
    except subprocess.CalledProcessError as e:
        print(f"Basic extraction failed: {e}")
        print("STDOUT:", e.stdout)
        print("STDERR:", e.stderr)
        error_folder = os.getenv('ERROR_FOLDER', '/app/errors')
        error_file = os.path.join(error_folder, f"{base_name}_basic_extract_error.txt")
        with open(error_file, 'w') as ef:
            ef.write(f"Basic Extraction Error\nSTDOUT:\n{e.stdout}\n\nSTDERR:\n{e.stderr}\n")
        return False
    
    # Step 3: Extract detailed information
    print("\\n=== Step 3: Detailed Information Extraction ===")
    
    try:
        result = subprocess.run([
            sys.executable, "extract_po_details.py"
        ], capture_output=True, text=True, check=True)
        print("Detailed extraction completed")
        print(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"Detailed extraction failed: {e}")
        print("STDOUT:", e.stdout)
        print("STDERR:", e.stderr)
        error_folder = os.getenv('ERROR_FOLDER', '/app/errors')
        error_file = os.path.join(error_folder, f"{base_name}_detail_extract_error.txt")
        with open(error_file, 'w') as ef:
            ef.write(f"Detail Extraction Error\nSTDOUT:\n{e.stdout}\n\nSTDERR:\n{e.stderr}\n")
        return False
    
    # Step 4: FileMaker Integration
    print("\\n=== Step 4: FileMaker Integration ===")
    
    filemaker_enabled = os.getenv('FILEMAKER_ENABLED', 'false').lower() == 'true'
    if filemaker_enabled:
        try:
            # Find the generated JSON file
            po_folders = [d for d in Path('.').iterdir() if d.is_dir() and d.name.startswith('455')]
            
            if po_folders:
                latest_po_folder = max(po_folders, key=lambda d: d.stat().st_mtime)
                json_file = latest_po_folder / f"{latest_po_folder.name}_info.json"
                
                if json_file.exists():
                    with open(json_file, 'r') as f:
                        po_data = json.load(f)
                    
                    # Create FileMaker record
                    print("🔄 Creating FileMaker record...")
                    fm = FileMakerIntegration()
                    
                    # Check if PO already exists to avoid duplicates
                    if not fm.check_duplicate_po(po_data.get('purchase_order_number')):
                        success = fm.insert_po_data(po_data)
                        
                        if success:
                            print(f"✅ PO {po_data.get('purchase_order_number')} successfully added to FileMaker")
                            # Update JSON with FileMaker status
                            po_data['filemaker_status'] = 'success'
                            po_data['filemaker_timestamp'] = datetime.now().isoformat()
                            # Telemetry from last FM call
                            po_data['filemaker_status_code'] = fm.last_status_code
                            po_data['filemaker_response'] = fm.last_response_text
                            po_data['filemaker_script_error'] = fm.last_script_error
                            po_data['filemaker_script_result'] = fm.last_script_result
                            po_data['filemaker_record_id'] = fm.last_record_id
                            # Send success notification via Dashboard API
                            try:
                                urls_env = os.getenv(
                                    "DASHBOARD_URLS",
                                    "https://192.168.0.62:9443/api/notifications/send,https://127.0.0.1:9443/api/notifications/send",
                                )
                                dashboard_urls = [u.strip() for u in urls_env.split(",") if u.strip()]
                                user = os.getenv("DASHBOARD_AUTH_USER", "anthony")
                                pwd = os.getenv("DASHBOARD_AUTH_PASS", "password")
                                auth = base64.b64encode(f"{user}:{pwd}".encode("utf-8")).decode("ascii")
                                headers = {"Authorization": f"Basic {auth}", "Content-Type": "application/json"}
                                payload = {
                                    "title": f"✅ FileMaker record created for PO {po_data.get('purchase_order_number')}",
                                    "message": f"PO {po_data.get('purchase_order_number')} created. scriptErr={fm.last_script_error}",
                                    "po_number": po_data.get('purchase_order_number'),
                                    "type": "success",
                                }
                                for url in dashboard_urls:
                                    try:
                                        r = requests.post(url, json=payload, headers=headers, timeout=10, verify=False)
                                        if r.status_code == 200:
                                            print(f"Dashboard notified: {url}")
                                            break
                                    except Exception as e:
                                        print(f"Dashboard notify failed via {url}: {e}")
                            except Exception as notify_err:
                                print(f"Notification error: {notify_err}")
                        else:
                            print(f"❌ Failed to add PO {po_data.get('purchase_order_number')} to FileMaker")
                            po_data['filemaker_status'] = 'failed'
                            # Telemetry from last FM call
                            po_data['filemaker_status_code'] = fm.last_status_code
                            po_data['filemaker_response'] = fm.last_response_text
                            po_data['filemaker_error'] = fm.last_error
                            po_data['filemaker_script_error'] = fm.last_script_error
                            po_data['filemaker_script_result'] = fm.last_script_result
                            # Send error notification via Dashboard API
                            try:
                                urls_env = os.getenv(
                                    "DASHBOARD_URLS",
                                    "https://192.168.0.62:9443/api/notifications/send,https://127.0.0.1:9443/api/notifications/send",
                                )
                                dashboard_urls = [u.strip() for u in urls_env.split(",") if u.strip()]
                                user = os.getenv("DASHBOARD_AUTH_USER", "anthony")
                                pwd = os.getenv("DASHBOARD_AUTH_PASS", "password")
                                auth = base64.b64encode(f"{user}:{pwd}".encode("utf-8")).decode("ascii")
                                headers = {"Authorization": f"Basic {auth}", "Content-Type": "application/json"}
                                payload = {
                                    "title": f"❌ FileMaker Error for PO {po_data.get('purchase_order_number')}",
                                    "message": f"Failed FM for PO {po_data.get('purchase_order_number')} (status={fm.last_status_code}, scriptErr={fm.last_script_error})",
                                    "po_number": po_data.get('purchase_order_number'),
                                    "type": "error",
                                }
                                for url in dashboard_urls:
                                    try:
                                        r = requests.post(url, json=payload, headers=headers, timeout=10, verify=False)
                                        if r.status_code == 200:
                                            print(f"Dashboard notified: {url}")
                                            break
                                    except Exception as e:
                                        print(f"Dashboard notify failed via {url}: {e}")
                            except Exception as notify_err:
                                print(f"Notification error: {notify_err}")
                    else:
                        print(f"⚠️ PO {po_data.get('purchase_order_number')} already exists in FileMaker")
                        po_data['filemaker_status'] = 'duplicate'
                    
                    # Save updated JSON
                    with open(json_file, 'w') as f:
                        json.dump(po_data, f, indent=2)
                        
                else:
                    print(f"❌ JSON file not found: {json_file}")
            else:
                print("❌ No PO folder found for FileMaker integration")
                
        except Exception as e:
            print(f"❌ FileMaker integration error: {e}")
    else:
        print("⚠️ FileMaker integration disabled (set FILEMAKER_ENABLED=true to enable)")
    
    print("\\nPO processing complete - awaiting Dashboard approval for FileMaker submission!")
    return True

def watch_folder(watch_path, processed_path=None):
    """
    Future implementation for folder monitoring
    This will watch for new PDF files and process them automatically
    """
    print(f"Folder monitoring will be implemented here for: {watch_path}")
    print("This will:")
    print("- Monitor folder for new PDF files")
    print("- Automatically process each new PDF")
    print("- Move completed folders to processed location")
    print("- Log all activities")
    print("- Handle errors gracefully")
    
    # For NAS deployment, this would use:
    # - watchdog library for file system monitoring
    # - Threading for concurrent processing
    # - Logging for audit trails
    # - Error handling and retry logic

def main():
    """Main function - can process single file or start folder monitoring"""
    if len(sys.argv) < 2:
        print("Complete PO Processing Pipeline")
        print("\\nUsage:")
        print("  Single file:    python process_po_complete.py input.pdf")
        print("  Folder watch:   python process_po_complete.py --watch /path/to/folder")
        print("\\nThis script will:")
        print("  1. Convert PDF to searchable PDF with OCR")
        print("  2. Extract all PO information to JSON")
        print("  3. Split PDF into PO and Router sections")
        print("  4. Organize files in PO-numbered folder")
        sys.exit(1)
    
    if sys.argv[1] == "--watch":
        if len(sys.argv) < 3:
            print("Error: Please specify folder path for monitoring")
            sys.exit(1)
        watch_folder(sys.argv[2])
    else:
        # Single file processing
        input_file = sys.argv[1]
        success = process_pdf_file(input_file)
        sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()