# FileMaker Error 800 Troubleshooting Guide

## Current Status: Error 800 Persistent

The PDFTimesheet script is consistently returning error 800 regardless of:
- File path format (absolute, relative, simple filename)
- Script parameters (complex, simple, or none)
- Different directory locations

This indicates the issue is **within the FileMaker script itself**, not the API integration.

## Error 800 Common Causes

### 1. Script Step Issues
Check your PDFTimesheet script for these potential problems:

#### A. Invalid Script Steps
```filemaker
# Make sure these steps are correct:
Go to Layout [ "Time Clock" ]  # Layout must exist and be accessible
Go to Record/Request/Page [ Get(ScriptParameter) ]  # Record ID must be valid
Save Records as PDF [ ... ]  # All parameters must be valid
```

#### B. Field Access Issues
```filemaker
# If your script references fields, make sure they exist:
Set Field [ SomeField ; SomeValue ]  # Field must exist on current layout
```

### 2. Layout and Record Issues

#### Check Layout Access
- Ensure "Time Clock" layout exists
- Verify the script has access to this layout
- Check if layout has any access restrictions

#### Check Record Navigation
- Verify record ID 57703 exists
- Make sure Go to Record step uses correct syntax
- Test with a known existing record

### 3. File Path and Save Issues

#### PDF Save Step
Your "Save Records as PDF" step should look like:
```filemaker
Save Records as PDF [
    Restore: No
    With dialog: Off
    Output file: $FilePath
    Records being browsed
    Include: All pages
]
```

#### Common PDF Save Problems:
- Invalid file path variable
- Missing file extension
- Insufficient permissions to write location
- Path contains invalid characters

### 4. Recommended Script Structure

Here's a basic PDFTimesheet script structure that should work:

```filemaker
# PDFTimesheet Script
# Parameter format: filename or full_path

# Set error capture
Set Error Capture [ On ]

# Get script parameter
Set Variable [ $FilePath ; Get(ScriptParameter) ]

# Set default path if none provided
If [ IsEmpty($FilePath) ]
    Set Variable [ $FilePath ; Get(DocumentsPath) & "test.pdf" ]
End If

# Go to Time Clock layout
Go to Layout [ "Time Clock" ]

# Save current record as PDF
Save Records as PDF [
    Restore: No
    With dialog: Off
    Output file: $FilePath
    Current record
]

# Check for errors
If [ Get(LastError) ≠ 0 ]
    Exit Script [ Text Result: "Error: " & Get(LastError) ]
Else
    Exit Script [ Text Result: "Success: " & $FilePath ]
End If
```

### 5. Debugging Steps

#### A. Add Debug Output
Add these steps to your script to see what's happening:
```filemaker
Show Custom Dialog [ "Debug" ; "Parameter: " & Get(ScriptParameter) ]
Show Custom Dialog [ "Debug" ; "Current Layout: " & Get(LayoutName) ]
Show Custom Dialog [ "Debug" ; "Record Count: " & Get(FoundCount) ]
```

#### B. Test Manually in FileMaker Pro
1. Open FileMaker Pro
2. Go to Scripts → Script Workspace
3. Find PDFTimesheet script
4. Run it manually with parameter: "test.pdf"
5. See what specific error occurs

#### C. Simplify the Script
Create a minimal test version:
```filemaker
# Minimal Test Script
Set Error Capture [ On ]
Save Records as PDF [ 
    Restore: No
    With dialog: Off  
    Output file: Get(DocumentsPath) & "simple_test.pdf"
    Current record
]
Exit Script [ Text Result: Get(LastError) ]
```

### 6. Alternative Approach: Print to PDF

If Save Records as PDF continues to fail, try Print step instead:
```filemaker
Print [
    Restore: No
    With dialog: Off
    Print to: PDF
    Output file: $FilePath
]
```

### 7. Next Steps

1. **Test script manually** in FileMaker Pro first
2. **Add debug dialogs** to see what values the script receives
3. **Simplify the script** to minimal PDF save operation
4. **Check FileMaker Server logs** for more detailed error information
5. **Verify layout and field access** permissions

The API integration is working perfectly - the issue is entirely within the FileMaker script logic.

## Test Commands Available

After fixing the script, you can test with:
```bash
# Test the updated script
python3 /volume1/Main/Main/ParkerPOsOCR/dashboard/test_pdf_export.py

# Test via web API
curl -k "https://your-server/api/filemaker/export_pdf/57703"
```
