#!/usr/bin/env python3
"""
PDF Auto-Print Monitor for Mac
Monitors /Users/Shared/ParkerPOsOCR/exports/ and automatically prints new PDF files
"""
import time
import os
import subprocess
import sys
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class PDFPrintHandler(FileSystemEventHandler):
    """Handler for PDF file creation events"""
    
    def __init__(self):
        self.printed_files = set()
        self.watch_dir = "/Users/Shared/ParkerPOsOCR/exports"
        self.printed_dir = "/Users/Shared/ParkerPOsOCR/exports/printed"
        self.last_seen_times = {}
        # CUPS printing options candidates (first that works will be used)
        env_opts = os.environ.get("CUPS_OPTIONS", "").strip()
        if env_opts:
            # honor environment override (split on spaces)
            self.lp_option_sets = [env_opts.split()]
        else:
            # Prefer fit-to-page on Letter, then generic fit options, then scaling fallback
            self.lp_option_sets = [
                ['-o', 'fit-to-page', '-o', 'media=Letter'],
                ['-o', 'fit-to-page'],
                ['-o', 'fitplot'],                     # legacy option name on some drivers
                ['-o', 'scaling=95'],                  # safe shrink fallback
            ]
        
        # Create printed directory if it doesn't exist
        self.ensure_printed_directory()
        
        print(f"📁 Monitoring directory: {self.watch_dir}")
        print(f"📂 Printed files moved to: {self.printed_dir}")
        print(f"🖨️ Default printer: {self.get_default_printer()}")
    
    def ensure_printed_directory(self):
        """Create the printed directory if it doesn't exist"""
        try:
            os.makedirs(self.printed_dir, exist_ok=True)
            print(f"📂 Ensured printed directory exists: {self.printed_dir}")
        except Exception as e:
            print(f"⚠️ Could not create printed directory: {e}")
        
    def get_default_printer(self):
        """Get the default printer name"""
        try:
            result = subprocess.run(['lpstat', '-d'], capture_output=True, text=True)
            if result.returncode == 0:
                # Parse output like "system default destination: hp_LaserJet_4200"
                for line in result.stdout.split('\n'):
                    if 'default destination:' in line:
                        return line.split('default destination:')[1].strip()
            return "Unknown"
        except Exception:
            return "Unknown"
    
    def on_created(self, event):
        """Called when a file is created"""
        if event.is_directory:
            return
        
        file_path = event.src_path
        
        # Only process PDF files
        if not file_path.lower().endswith('.pdf'):
            return
            
        # Avoid duplicate processing
        if file_path in self.printed_files:
            return
            
        print(f"\n📄 New PDF detected: {os.path.basename(file_path)}")
        # Wait for file to be fully written and stable
        if self.wait_for_file_ready(file_path):
            # Print the PDF
            self.print_pdf(file_path)
        else:
            print("⚠️ File did not become ready in time; skipping this event")
        
        # Mark as processed
        self.printed_files.add(file_path)
    
    def on_modified(self, event):
        """Called when a file is modified - also try to print in case creation was missed"""
        if event.is_directory:
            return
            
        file_path = event.src_path
        
        # Only process PDF files that haven't been printed yet
        if file_path.lower().endswith('.pdf') and file_path not in self.printed_files:
            # Debounce frequent modify events
            now = time.time()
            last = self.last_seen_times.get(file_path, 0)
            if now - last < 1.0:
                return
            self.last_seen_times[file_path] = now

            print(f"\n📄 PDF modified/completed: {os.path.basename(file_path)}")
            if self.wait_for_file_ready(file_path):
                self.print_pdf(file_path)
                self.printed_files.add(file_path)
            else:
                print("⚠️ File not yet ready; will wait for next modify event")

    def wait_for_file_ready(self, file_path, checks: int = 4, interval: float = 0.5) -> bool:
        """Ensure file size is stable and file is readable before printing"""
        try:
            prev_size = -1
            stable_count = 0
            for _ in range(checks):
                if not os.path.exists(file_path):
                    time.sleep(interval)
                    continue
                size = os.path.getsize(file_path)
                if size > 0 and size == prev_size:
                    stable_count += 1
                else:
                    stable_count = 0
                prev_size = size
                # Try to open the file for reading to ensure no exclusive lock
                try:
                    with open(file_path, 'rb') as f:
                        head = f.read(5)
                        # Basic PDF header check
                        if head != b'%PDF-':
                            pass
                except Exception:
                    stable_count = 0
                if stable_count >= 2:
                    return True
                time.sleep(interval)
        except Exception as e:
            print(f"⚠️ File readiness check error: {e}")
        return False
    
    def print_pdf(self, file_path):
        """Print a PDF file and move it to printed folder"""
        try:
            print(f"🖨️ Sending to printer: {os.path.basename(file_path)}")

            last_error = None
            result = None
            used_args = None
            for opts in self.lp_option_sets:
                args = ['lp'] + opts + [file_path]
                used_args = args
                result = subprocess.run(args, capture_output=True, text=True, timeout=30)
                if result.returncode == 0:
                    break
                last_error = result.stderr.strip()
            
            if result and result.returncode == 0:
                # Parse job ID from output
                job_info = result.stdout.strip()
                print(f"✅ Print job submitted: {job_info}")
                if used_args:
                    print(f"   Options: {' '.join(used_args[1:-1])}")
                
                # Log the print job
                self.log_print_job(file_path, job_info)
                
                # Move file to printed directory
                self.move_to_printed_folder(file_path)
                
            else:
                err = last_error or (result.stderr.strip() if result else 'Unknown error')
                print(f"❌ Print failed: {err}")
                self.log_print_job(file_path, f"PRINT_FAILED: {err}")
                
        except subprocess.TimeoutExpired:
            print("⚠️ Print command timed out")
            self.log_print_job(file_path, "PRINT_TIMEOUT")
        except Exception as e:
            print(f"❌ Print error: {str(e)}")
            self.log_print_job(file_path, f"PRINT_ERROR: {str(e)}")
    
    def move_to_printed_folder(self, file_path):
        """Move printed PDF to the printed subfolder"""
        try:
            import shutil
            filename = os.path.basename(file_path)
            destination = os.path.join(self.printed_dir, filename)
            
            # Move the file
            shutil.move(file_path, destination)
            print(f"📂 Moved to printed folder: {filename}")
            
        except Exception as e:
            print(f"⚠️ Could not move file to printed folder: {e}")
    
    def log_print_job(self, file_path, job_info):
        """Log print jobs to a file"""
        log_file = "/Users/Shared/ParkerPOsOCR/print_log.txt"
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"{timestamp} - Printed: {os.path.basename(file_path)} - {job_info}\n"
        
        try:
            with open(log_file, 'a') as f:
                f.write(log_entry)
        except Exception as e:
            print(f"⚠️ Could not write to log file: {e}")
    
    def scan_existing_files(self, auto_mode=False):
        """Check for existing PDF files that might need printing"""
        print("🔍 Scanning for existing PDF files...")
        
        try:
            for file_path in Path(self.watch_dir).glob("*.pdf"):
                file_path_str = str(file_path)
                if file_path_str not in self.printed_files:
                    print(f"📄 Found existing PDF: {file_path.name}")
                    
                    if auto_mode:
                        # In auto mode, attempt to print existing files that are not already in the printed folder
                        printed_candidate = os.path.join(self.printed_dir, file_path.name)
                        if os.path.exists(printed_candidate):
                            print(f"↪️ Already printed previously, skipping: {file_path.name}")
                        else:
                            if self.wait_for_file_ready(file_path_str):
                                print(f"🤖 Auto mode: Printing existing file {file_path.name}")
                                self.print_pdf(file_path_str)
                            else:
                                print(f"⚠️ Existing file not ready yet, will rely on modify events: {file_path.name}")
                    else:
                        # Ask user if they want to print existing files
                        response = input(f"Print {file_path.name}? (y/n): ").lower().strip()
                        if response == 'y':
                            self.print_pdf(file_path_str)
                    
                    # Mark as seen regardless
                    self.printed_files.add(file_path_str)
                    
        except Exception as e:
            print(f"⚠️ Error scanning existing files: {e}")

def main():
    """Main monitoring function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='PDF Auto-Print Monitor')
    parser.add_argument('--auto', action='store_true', 
                       help='Auto mode: skip existing files without prompting')
    args = parser.parse_args()
    
    watch_directory = "/Users/Shared/ParkerPOsOCR/exports"
    
    # Check if directory exists
    if not os.path.exists(watch_directory):
        print(f"❌ Directory does not exist: {watch_directory}")
        sys.exit(1)
    
    print("🎯 PDF Auto-Print Monitor Starting...")
    print("=" * 50)
    
    # Create event handler and observer
    event_handler = PDFPrintHandler()
    observer = Observer()
    observer.schedule(event_handler, watch_directory, recursive=False)
    
    # Check for existing files first
    event_handler.scan_existing_files(auto_mode=args.auto)
    
    # Start monitoring
    observer.start()
    print(f"\n👀 Monitoring started... Press Ctrl+C to stop")
    print(f"📁 Watching: {watch_directory}")
    print("🖨️ Auto-printing enabled for new PDF files")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print(f"\n🛑 Monitoring stopped by user")
        observer.stop()
    
    observer.join()
    print("👋 PDF Auto-Print Monitor stopped")

if __name__ == "__main__":
    main()
