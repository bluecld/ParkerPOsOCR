# FileMaker Barcode Generator Plugin Setup Guide

## Overview
This guide covers setting up the RefreshBarcodes script to work with FileMaker Barcode Generator plugin container fields.

## Understanding Barcode Generator Plugin

The FileMaker Barcode Generator plugin typically works with:
- **Text fields** that contain the data to encode (e.g., PO numbers, part numbers)
- **Container fields** that use plugin calculations to generate barcode images
- **Auto-enter calculations** or **scripts** that populate the container fields

## Required FileMaker Script: RefreshBarcodes

Create this script in your FileMaker database:

```
# RefreshBarcodes Script
# Purpose: Refresh barcode container fields after API record creation

# Parse script parameter
Set Variable [$param; Value: Get(ScriptParameter)]
Set Variable [$recordId; Value: JSONGetElement($param; "record_id")]
Set Variable [$layout; Value: JSONGetElement($param; "layout")]

# The record ID passed is from PreInventory, but barcodes are on Time Clock Reduced layout
# We need to find the corresponding record in the main table

# Method 1: If there's a relationship between PreInventory and main table
Go to Layout ["PreInventory"]
Go to Record/Request/Page [$recordId]

# Get the PO number or other identifier to find the main record
Set Variable [$poNumber; Value: PreInventory::Whittaker Shipper #]

# Go to the layout with barcodes
Go to Layout ["Time Clock Reduced"]

# Find the corresponding record by PO number
Enter Find Mode [Pause: Off]
Set Field [Whittaker Shipper #; $poNumber]  # Adjust field name as needed
Perform Find []

If [Get(FoundCount) > 0]
    # Go to the found record
    Go to Record/Request/Page [First]
    
    # Method A: Force window refresh to trigger plugin recalculation
    Refresh Window [Flush cached join results; Flush cached SQL data]
    
    # Method B: Update container fields that use Barcode Generator plugin
    # Replace these field names with your actual barcode container fields:
    
    # Example for PO Number barcode:
    Set Field [BarcodeContainer_PO; 
        Code128("" & Whittaker Shipper # & "")]
    
    # Example for Part Number barcode:
    Set Field [BarcodeContainer_Part; 
        Code39("" & Part Number & "")]
    
    # Example for Quantity barcode:
    Set Field [BarcodeContainer_Qty; 
        Code93("" & Quantity & "")]
    
    # Commit the changes
    Commit Records/Requests [Skip data entry validation; No dialog]
    
    # Return success
    Exit Script [Text Result: "Barcode refresh completed for PO " & $poNumber]
Else
    # Record not found in main table
    Exit Script [Text Result: "Main record for PO " & $poNumber & " not found"]
End If
```

## Common Barcode Generator Plugin Functions

Replace the plugin functions in the script above with the ones you're using:

- `Code39(text)` - Code 39 barcodes
- `Code128(text)` - Code 128 barcodes  
- `Code93(text)` - Code 93 barcodes
- `DataMatrix(text)` - Data Matrix codes
- `QRCode(text)` - QR codes
- `UPC_A(text)` - UPC-A barcodes
- `EAN13(text)` - EAN-13 barcodes

## Container Field Setup

Your container fields should have calculations like:

```
# For PO Number barcode container:
Code128(PONumber)

# For Part Number barcode container:  
Code39(PartNumber)

# For Quantity barcode container:
Code93(Quantity)
```

## Alternative Approaches

### Option 1: Auto-Enter Calculations
Set your barcode container fields to have auto-enter calculations that reference the text fields:

1. Field Options → Auto-Enter → Calculated value
2. Formula: `Code128(PONumber)` (adjust as needed)
3. Check "Do not replace existing value" if needed

### Option 2: Field Triggers  
Add OnObjectModify triggers to your text fields that update the barcode containers:

```
# OnObjectModify script for PONumber field:
Set Field [BarcodeContainer_PO; Code128(PONumber)]
Commit Records/Requests [No dialog]
```

### Option 3: Layout Triggers
Add OnRecordLoad trigger to your timesheet layout:

```
# OnRecordLoad script:
Refresh Window
Set Field [BarcodeContainer_PO; Code128(PONumber)]
Set Field [BarcodeContainer_Part; Code39(PartNumber)]  
Set Field [BarcodeContainer_Qty; Code93(Quantity)]
```

## Debugging Steps

1. **Test the plugin manually**: 
   - Create a new record in FileMaker
   - Enter data in text fields
   - Check if barcode containers populate automatically

2. **Verify field names**:
   - Make sure the Python script uses correct field names
   - Check that container fields exist in the timesheet layout

3. **Test the RefreshBarcodes script**:
   - Run it manually from FileMaker Script Workspace
   - Pass test parameters: `{"record_id": "123", "layout": "timesheet"}`

4. **Check plugin licensing**:
   - Ensure Barcode Generator plugin is properly licensed
   - Verify it's installed on FileMaker Server (not just client)

## Python Integration Notes

The updated `refresh_barcodes()` method will:

1. **Primary method**: Call your RefreshBarcodes script with record ID
2. **Fallback method**: Update timestamp fields to trigger recalculation
3. **Error handling**: Log success/failure for debugging

## Expected Behavior

After API record creation:
1. Python calls `refresh_barcodes(record_id)`
2. RefreshBarcodes script runs in FileMaker
3. Container fields populate with barcode images
4. Barcodes visible on timesheet layout/printed PDFs

## Troubleshooting

- **No barcodes appear**: Check plugin installation and licensing
- **Script errors**: Verify field names and layout names in script
- **API errors**: Check FileMaker script permissions and parameter format
- **Partial refresh**: Some containers may need individual field updates
