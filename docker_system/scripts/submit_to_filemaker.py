#!/usr/bin/env python3
"""
FileMaker Submission Script
Called by Dashboard when user approves a PO for FileMaker submission
"""

import json
import sys
import os
from pathlib import Path
from datetime import datetime

# Add the scripts directory to the path so we can import filemaker_integration
sys.path.append('/app')

def submit_po_to_filemaker(po_number, force_resubmit=False):
    """Submit a specific PO to FileMaker after approval"""
    
    try:
        from filemaker_integration import FileMakerIntegration
        
        # Find the PO folder and JSON file
        po_folder = Path(f'/app/processed/{po_number}')
        if not po_folder.exists():
            return {"success": False, "error": f"PO folder not found: {po_folder}"}
        
        json_file = po_folder / f"{po_number}_info.json"
        if not json_file.exists():
            return {"success": False, "error": f"JSON file not found: {json_file}"}
        
        # Load PO data
        with open(json_file, 'r') as f:
            po_data = json.load(f)
        
        # Hard guard: allow users to mark a PO as do-not-resubmit
        if not force_resubmit and po_data.get('filemaker_no_resubmit'):
            return {"success": False, "error": "Resubmission disabled for this PO (filemaker_no_resubmit). Use --force to override."}

        # If already submitted once, avoid auto re-creating records unless --force
        if not force_resubmit and po_data.get('filemaker_submitted'):
            return {"success": False, "error": "PO was already submitted; use --force to resubmit"}
        
        # Check if FileMaker is enabled
        filemaker_enabled = os.getenv('FILEMAKER_ENABLED', 'false').lower() == 'true'
        
        if filemaker_enabled:
            # Initialize FileMaker integration
            fm = FileMakerIntegration()
            
            # Authenticate
            if not fm.authenticate():
                return {"success": False, "error": "FileMaker authentication failed"}
            
            try:
                # If the JSON indicates it was previously submitted, but the record no longer exists,
                # do NOT recreate automatically unless --force. Mark a no-resubmit flag so deletion sticks.
                if not force_resubmit and po_data.get('filemaker_status') == 'success':
                    exists_now = fm.check_duplicate_po(po_number)
                    if not exists_now:
                        po_data['filemaker_no_resubmit'] = True
                        po_data['filemaker_submitted'] = False
                        po_data['filemaker_status'] = 'deleted'
                        po_data['filemaker_deleted_timestamp'] = datetime.now().isoformat()
                        with open(json_file, 'w') as f:
                            json.dump(po_data, f, indent=2)
                        return {"success": False, "error": "FileMaker record was deleted; will not recreate automatically (set filemaker_no_resubmit). Use --force to recreate."}

                # Check for duplicates
                if fm.check_duplicate_po(po_number):
                    # Update approval status but note duplicate
                    po_data['approval_status'] = 'approved'
                    po_data['approved_timestamp'] = datetime.now().isoformat()
                    po_data['filemaker_submitted'] = False
                    po_data['filemaker_error'] = 'Duplicate PO exists in FileMaker'
                    po_data['filemaker_status'] = 'duplicate'
                    
                    with open(json_file, 'w') as f:
                        json.dump(po_data, f, indent=2)
                    
                    return {"success": False, "error": f"PO {po_number} already exists in FileMaker"}
                
                # Insert PO data
                result = fm.insert_po_data(po_data)
                
                if result:
                    # Update approval status and submission status
                    po_data['approval_status'] = 'approved'
                    po_data['approved_timestamp'] = datetime.now().isoformat()
                    po_data['filemaker_submitted'] = True
                    po_data['filemaker_submission_timestamp'] = datetime.now().isoformat()
                    po_data['filemaker_status'] = 'success'
                    # Clear no-resubmit flag on a successful forced re-create
                    if 'filemaker_no_resubmit' in po_data:
                        po_data.pop('filemaker_no_resubmit', None)
                    # Telemetry from last FM call
                    po_data['filemaker_status_code'] = fm.last_status_code
                    po_data['filemaker_response'] = fm.last_response_text
                    po_data['filemaker_script_error'] = fm.last_script_error
                    po_data['filemaker_script_result'] = fm.last_script_result
                    po_data['filemaker_record_id'] = fm.last_record_id
                    
                    with open(json_file, 'w') as f:
                        json.dump(po_data, f, indent=2)
                    
                    return {"success": True, "message": f"PO {po_number} successfully submitted to FileMaker"}
                else:
                    # Capture telemetry on failure as well
                    po_data['filemaker_submitted'] = False
                    po_data['filemaker_status'] = 'failed'
                    po_data['filemaker_status_code'] = fm.last_status_code
                    po_data['filemaker_response'] = fm.last_response_text
                    po_data['filemaker_error'] = fm.last_error
                    po_data['filemaker_script_error'] = fm.last_script_error
                    po_data['filemaker_script_result'] = fm.last_script_result
                    with open(json_file, 'w') as f:
                        json.dump(po_data, f, indent=2)
                    return {"success": False, "error": "FileMaker submission failed"}
                
            finally:
                # Always logout
                fm.logout()
        else:
            # Mock mode - just update the approval status
            po_data['approval_status'] = 'approved'
            po_data['approved_timestamp'] = datetime.now().isoformat()
            po_data['filemaker_submitted'] = True
            po_data['filemaker_submission_timestamp'] = datetime.now().isoformat()
            po_data['filemaker_mode'] = 'mock'
            
            with open(json_file, 'w') as f:
                json.dump(po_data, f, indent=2)
            
            return {"success": True, "message": f"PO {po_number} approved (FileMaker disabled - mock mode)"}
            
    except ImportError:
        return {"success": False, "error": "FileMaker integration module not available"}
    except Exception as e:
        return {"success": False, "error": f"FileMaker submission error: {str(e)}"}

def main():
    """Main function for command line usage"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Submit PO to FileMaker')
    parser.add_argument('po_number', help='PO number to submit')
    parser.add_argument('--force', action='store_true', help='Force resubmission even if already submitted')
    
    args = parser.parse_args()
    
    result = submit_po_to_filemaker(args.po_number, args.force)
    
    if result["success"]:
        print(f"✅ {result['message']}")
        sys.exit(0)
    else:
        print(f"❌ {result['error']}")
        sys.exit(1)

if __name__ == "__main__":
    main()
