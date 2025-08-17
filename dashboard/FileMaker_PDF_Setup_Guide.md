# FileMaker PDFTimesheet Script Configuration Guide

## Current Status
- ✅ API integration working - script executes successfully
- ✅ Mac file path format implemented: `/Users/Shared/ParkerPOsOCR/exports/filename.pdf`
- ❌ FileMaker script returns error 800

## Error 800 Solutions

### 1. Check Folder Permissions on Mac Server
The FileMaker server needs write access to the export folder:

```bash
# On the Mac server, create the folder and set permissions:
sudo mkdir -p /Users/Shared/ParkerPOsOCR/exports
sudo chmod 777 /Users/Shared/ParkerPOsOCR/exports
sudo chown fmserver:fmserver /Users/Shared/ParkerPOsOCR/exports
```

### 2. FileMaker Script Requirements
Your PDFTimesheet script should handle these elements:

#### Script Parameter Format
The API passes: `record_id|layout_name|file_path`
Example: `57703|Time Clock|/Users/Shared/ParkerPOsOCR/exports/record_57703_20250814_171211.pdf`

#### Recommended Script Steps:
```filemaker
# Parse script parameter
Set Variable [ $RecordID ; Get(ScriptParameter) ]
Set Variable [ $Params ; Substitute($RecordID ; "|" ; "¶") ]
Set Variable [ $RecordID ; GetValue($Params ; 1) ]
Set Variable [ $Layout ; GetValue($Params ; 2) ]
Set Variable [ $FilePath ; GetValue($Params ; 3) ]

# Go to the correct record and layout
Go to Layout [ $Layout ]
Go to Record/Request/Page [ $RecordID ]

# Save as PDF
Save Records as PDF [ Restore ; With dialog: Off ; $FilePath ; Records being browsed ]

# Set script result for API feedback
Exit Script [ Text Result: "success" ]
```

### 3. Alternative File Paths to Try

If `/Users/Shared/` doesn't work, try these paths in the FileMaker script:

#### Option A: FileMaker Documents folder
```
Get(DocumentsPath) & "ParkerPOsOCR/exports/" & filename
```

#### Option B: Desktop
```
Get(DesktopPath) & "ParkerPOsOCR/" & filename
```

#### Option C: Temporary folder
```
Get(TemporaryPath) & filename
```

### 4. Script Debugging Steps

1. **Add Show Custom Dialog steps** in your script to see what values are being received:
   ```filemaker
   Show Custom Dialog [ "Debug" ; "RecordID: " & $RecordID & "¶FilePath: " & $FilePath ]
   ```

2. **Test the script manually** in FileMaker Pro with the same parameters

3. **Check FileMaker Server logs** for more detailed error information

### 5. Current API Integration

The API now sends Mac-compatible paths:
- Default export path: `/Users/Shared/ParkerPOsOCR/exports/`
- File naming: `record_{record_id}_{timestamp}.pdf`
- Full path example: `/Users/Shared/ParkerPOsOCR/exports/record_57703_20250814_171211.pdf`

### 6. Testing from FileMaker Pro

To test your script manually:
1. Go to Scripts menu → Script Workspace
2. Find your PDFTimesheet script  
3. Run with parameter: `57703|Time Clock|/Users/Shared/ParkerPOsOCR/exports/test.pdf`
4. Check if the PDF is created successfully

### 7. Error Code Reference
- Error 800: Usually file/folder access issues
- Error 100: File missing
- Error 200: Record access problem

## Next Steps
1. Create the export folder with proper permissions on Mac server
2. Test the PDFTimesheet script manually in FileMaker Pro
3. Check FileMaker Server logs for more details
4. Once working manually, the API integration should work automatically
