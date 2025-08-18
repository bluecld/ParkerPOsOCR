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
from pathlib import Path
from datetime import datetime
from filemaker_integration import FileMakerIntegration

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
    except subprocess.CalledProcessError as e:
        print(f"OCR processing failed: {e}")
        print("STDOUT:", e.stdout)
        print("STDERR:", e.stderr)
        return False
    
    # Step 2: Extract PO information and split PDF
    print("\\n=== Step 2: Information Extraction & PDF Splitting ===")
    
    # Modify the extract_po_info.py to use the correct filename temporarily
    import tempfile
    with open("extract_po_info.py", "r") as f:
        content = f.read()
    
    # Replace the default filename with our searchable PDF
    modified_content = content.replace(
        'input_pdf = os.environ.get("SEARCHABLE_PDF", "final_searchable_output.pdf")',
        f'input_pdf = "{searchable_pdf}"'
    )
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as temp_file:
        temp_file.write(modified_content)
        temp_script = temp_file.name
    
    try:
        result = subprocess.run([
            sys.executable, temp_script
        ], capture_output=True, text=True, check=True)
        print("Basic PO extraction completed")
    except subprocess.CalledProcessError as e:
        print(f"Basic extraction failed: {e}")
        print("STDOUT:", e.stdout)
        print("STDERR:", e.stderr)
        return False
    finally:
        os.unlink(temp_script)
    
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
                            # Send success notification
                            try:
                                from dashboard.notifications import notification_manager
                                notification_manager.send_notification(
                                    title=f"✅ FileMaker record created for PO {po_data.get('purchase_order_number')}",
                                    message=f"PO {po_data.get('purchase_order_number')} was successfully created in FileMaker.",
                                    po_number=po_data.get('purchase_order_number'),
                                    notification_type="success"
                                )
                            except Exception as notify_err:
                                print(f"Notification error: {notify_err}")
                        else:
                            print(f"❌ Failed to add PO {po_data.get('purchase_order_number')} to FileMaker")
                            po_data['filemaker_status'] = 'failed'
                            # Send error notification
                            try:
                                from dashboard.notifications import notification_manager
                                notification_manager.send_notification(
                                    title=f"❌ FileMaker Error for PO {po_data.get('purchase_order_number')}",
                                    message=f"Failed to create FileMaker record for PO {po_data.get('purchase_order_number')}",
                                    po_number=po_data.get('purchase_order_number'),
                                    notification_type="error"
                                )
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