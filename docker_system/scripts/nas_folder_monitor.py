"""
NAS Folder Monitor for Automated PO Processing
Designed for ASUSTOR NAS deployment

Features:
- Monitors folder for new PDF files
- Processes PDFs automatically  
- Moves completed work to organized folders
- Logs all activities
- Handles errors and retries
"""

import os
import sys
import time
import logging
import shutil
import requests
import json
from pathlib import Path
from datetime import datetime
try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
except ImportError:
    print("Please install watchdog: pip install watchdog")
    sys.exit(1)

class POProcessorHandler(FileSystemEventHandler):
    """Handles file system events for PO processing"""
    
    def __init__(self, watch_folder, output_folder, processed_folder, error_folder):
        self.watch_folder = Path(watch_folder)
        self.output_folder = Path(output_folder) 
        self.processed_folder = Path(processed_folder)
        self.error_folder = Path(error_folder)
        
        # Create folders if they don't exist
        for folder in [self.output_folder, self.processed_folder, self.error_folder]:
            folder.mkdir(parents=True, exist_ok=True)
    
    def send_notification(self, title, message, po_number=None, notification_type="info"):
        """Send notification to dashboard API"""
        try:
            # Try to send notification via dashboard API
            payload = {
                "title": title,
                "message": message,
                "po_number": po_number,
                "type": notification_type
            }
            
            # Dashboard URLs - try internal container networking first, then external
            dashboard_urls = [
                "https://dashboard:8443/api/notifications/send",  # Container network
                "https://192.168.0.62:8443/api/notifications/send",  # External access
                "https://127.0.0.1:8443/api/notifications/send"
            ]
            
            # Authentication for the dashboard API
            import base64
            auth_string = base64.b64encode(b"anthony:password").decode('ascii')
            headers = {
                'Authorization': f'Basic {auth_string}',
                'Content-Type': 'application/json'
            }
            
            for url in dashboard_urls:
                try:
                    # Use verify=False for HTTPS to handle self-signed certificates
                    verify_ssl = False if url.startswith('https://') else True
                    response = requests.post(url, json=payload, headers=headers, timeout=10, verify=verify_ssl)
                    if response.status_code == 200:
                        logging.info(f"Notification sent: {title}")
                        return True
                    else:
                        logging.warning(f"Notification failed with status {response.status_code}: {response.text}")
                except Exception as url_error:
                    logging.warning(f"Failed to reach {url}: {url_error}")
                    continue
            
            # If dashboard API fails, log it but don't stop processing
            logging.error(f"All notification URLs failed for: {title}")
            return False
                    
        except Exception as e:
            logging.error(f"Failed to send notification: {e}")
            return False
    
    def on_created(self, event):
        """Called when a file or directory is created"""
        if event.is_directory:
            return
            
        file_path = Path(event.src_path)
        
        # Only process PDF files
        if file_path.suffix.lower() == '.pdf':
            logging.info(f"New PDF detected: {file_path}")
            # Enhanced file completion check
            if self.wait_for_file_completion(file_path):
                self.process_pdf(file_path)
            else:
                logging.error(f"File completion timeout for: {file_path}")
                self.handle_failed_processing(file_path, "File was not completed within timeout period")
    
    def wait_for_file_completion(self, file_path, timeout=120, stable_time=10):
        """Wait for file to be completely written by monitoring size stability"""
        start_time = time.time()
        last_size = -1
        stable_start = None
        size_checks = []
        
        logging.info(f"Monitoring file completion: {file_path.name}")
        
        while time.time() - start_time < timeout:
            if not file_path.exists():
                logging.warning(f"File disappeared during monitoring: {file_path}")
                return False
                
            try:
                current_size = file_path.stat().st_size
                size_checks.append((time.time(), current_size))
                
                # Keep only last 20 size checks for analysis
                if len(size_checks) > 20:
                    size_checks = size_checks[-20:]
                
                # Enhanced multi-page scan detection
                if current_size > 5000000:  # > 5MB likely multi-page
                    required_stable_time = 15  # Longer wait for multi-page
                    logging.info(f"Large file detected ({current_size:,} bytes) - using extended stability period")
                else:
                    required_stable_time = stable_time  # Standard wait for single page
                
                if current_size == last_size and current_size > 0:
                    if stable_start is None:
                        stable_start = time.time()
                        logging.info(f"File size stable at {current_size:,} bytes, monitoring for {required_stable_time}s...")
                    elif time.time() - stable_start >= required_stable_time:
                        # Additional validation: check for PDF structure completeness
                        if self.validate_pdf_structure(file_path):
                            logging.info(f"File stable for {required_stable_time}s and PDF structure valid - ready for processing")
                            return True
                        else:
                            logging.warning(f"PDF structure incomplete despite stable size, continuing to monitor...")
                            stable_start = None  # Reset stability timer
                else:
                    if current_size != last_size:
                        elapsed = time.time() - start_time
                        logging.info(f"File growing: {last_size:,} -> {current_size:,} bytes (after {elapsed:.1f}s)")
                    stable_start = None
                    last_size = current_size
                    
                time.sleep(2)  # Check every 2 seconds for multi-page scans
                
            except OSError as e:
                logging.warning(f"OS Error accessing file (scanner may have lock): {e}")
                time.sleep(3)
        
        logging.error(f"File completion timeout after {timeout}s for: {file_path}")
        return False
    
    def validate_pdf_structure(self, file_path):
        """Validate that PDF has proper structure with pages"""
        try:
            import fitz
            pdf = fitz.open(str(file_path))
            page_count = len(pdf)
            pdf.close()
            
            if page_count > 0:
                logging.info(f"PDF validation: {page_count} pages found - structure complete")
                return True
            else:
                logging.warning(f"PDF validation: 0 pages found - scan likely incomplete")
                return False
                
        except Exception as e:
            logging.warning(f"PDF validation failed: {e} - assuming incomplete")
            return False
    
    def process_pdf(self, pdf_path):
        """Process a single PDF file"""
        try:
            logging.info(f"Starting processing: {pdf_path.name}")
            
            # Change to the directory containing the scripts
            original_cwd = os.getcwd()
            script_dir = Path(__file__).parent
            os.chdir(script_dir)
            
            # Import processing functions
            from process_po_complete import process_pdf_file
            
            # Process the PDF
            success = process_pdf_file(str(pdf_path))
            
            if success:
                self.handle_successful_processing(pdf_path)
            else:
                self.handle_failed_processing(pdf_path, "Processing failed")
                
        except Exception as e:
            logging.error(f"Error processing {pdf_path}: {e}")
            self.handle_failed_processing(pdf_path, str(e))
        finally:
            os.chdir(original_cwd)
    
    def handle_successful_processing(self, original_pdf):
        """Handle successful processing"""
        try:
            # Find the created PO folder
            script_dir = Path(__file__).parent
            po_folders = [d for d in script_dir.iterdir() if d.is_dir() and d.name.startswith('455')]
            
            if po_folders:
                # Get the most recently created PO folder
                latest_po_folder = max(po_folders, key=lambda d: d.stat().st_mtime)
                po_number = latest_po_folder.name
                
                # Move PO folder to output directory
                destination = self.output_folder / po_number
                if destination.exists():
                    shutil.rmtree(destination)
                shutil.move(str(latest_po_folder), str(destination))
                
                # Move original PDF to processed folder
                processed_pdf = self.processed_folder / f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{original_pdf.name}"
                shutil.move(str(original_pdf), str(processed_pdf))
                
                logging.info(f"Successfully processed PO {po_number}")
                logging.info(f"  - PO folder moved to: {destination}")
                logging.info(f"  - Original PDF moved to: {processed_pdf}")
                
                # Try to read additional PO details from JSON
                part_number = "Not extracted"
                quantity = "Not extracted"
                try:
                    json_file = destination / f"{po_number}_info.json"
                    if json_file.exists():
                        import json
                        with open(json_file, 'r') as f:
                            po_data = json.load(f)
                            part_number = po_data.get('part_number', 'Not extracted')
                            quantity = po_data.get('quantity', 'Not extracted')
                except Exception as e:
                    logging.warning(f"Could not read PO details: {e}")
                
                # Send enhanced success notification with part number and quantity
                self.send_notification(
                    title=f"✅ PO {po_number} Processed Successfully",
                    message=f"Purchase Order {po_number} has been successfully processed!\n\n📁 Original file: {original_pdf.name}\n📦 Part Number: {part_number}\n🔢 Quantity: {quantity}\n⏰ Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n📂 Data folder: {po_number}",
                    po_number=po_number,
                    notification_type="success"
                )
                
        except Exception as e:
            logging.error(f"Error in post-processing: {e}")
            self.handle_failed_processing(original_pdf, f"Post-processing error: {e}")
    
    def handle_failed_processing(self, original_pdf, error_message):
        """Handle failed processing"""
        try:
            # Move failed PDF to error folder with timestamp and error info
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            error_pdf = self.error_folder / f"{timestamp}_ERROR_{original_pdf.name}"
            shutil.move(str(original_pdf), str(error_pdf))
            
            # Create error log file
            error_log = error_pdf.with_suffix('.txt')
            with open(error_log, 'w') as f:
                f.write(f"Processing Error\\n")
                f.write(f"Timestamp: {datetime.now()}\\n")
                f.write(f"Original File: {original_pdf.name}\\n")
                f.write(f"Error: {error_message}\\n")
            
            logging.error(f"Failed to process {original_pdf.name}: {error_message}")
            logging.error(f"  - Moved to error folder: {error_pdf}")
            
            # Send error notification
            self.send_notification(
                title=f"❌ PO Processing Failed",
                message=f"Failed to process PDF file: {original_pdf.name}\\n\\n🚨 Error: {error_message}\\n⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\\n📁 Moved to: {error_pdf.name}",
                notification_type="error"
            )
            
        except Exception as e:
            logging.critical(f"Critical error in error handling: {e}")

def setup_logging(log_file):
    """Setup logging configuration"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )

def main():
    """Main monitoring function"""
    if len(sys.argv) != 5:
        print("NAS PO Processing Monitor")
        print("\\nUsage:")
        print("  python nas_folder_monitor.py <watch_folder> <output_folder> <processed_folder> <error_folder>")
        print("\\nExample:")
        print("  python nas_folder_monitor.py /volume1/incoming /volume1/processed /volume1/archive /volume1/errors")
        sys.exit(1)
    
    watch_folder = sys.argv[1]
    output_folder = sys.argv[2] 
    processed_folder = sys.argv[3]
    error_folder = sys.argv[4]
    
    # Setup logging
    log_file = Path(output_folder) / 'po_processor.log'
    setup_logging(log_file)
    
    # Validate folders
    if not os.path.exists(watch_folder):
        logging.error(f"Watch folder does not exist: {watch_folder}")
        sys.exit(1)
    
    logging.info("=== NAS PO Processing Monitor Started ===")
    logging.info(f"Watch folder: {watch_folder}")
    logging.info(f"Output folder: {output_folder}")
    logging.info(f"Processed folder: {processed_folder}")
    logging.info(f"Error folder: {error_folder}")
    
    # Setup file system monitoring
    event_handler = POProcessorHandler(watch_folder, output_folder, processed_folder, error_folder)
    observer = Observer()
    observer.schedule(event_handler, watch_folder, recursive=False)
    
    # Start monitoring
    observer.start()
    logging.info("Folder monitoring active - waiting for PDF files...")
    
    try:
        while True:
            time.sleep(10)  # Check every 10 seconds
    except KeyboardInterrupt:
        logging.info("Monitoring stopped by user")
        observer.stop()
    
    observer.join()
    logging.info("=== NAS PO Processing Monitor Stopped ===")

if __name__ == "__main__":
    main()