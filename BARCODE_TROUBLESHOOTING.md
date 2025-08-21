# Barcode Refresh Troubleshooting

## The Problem
The RefreshBarcodes script isn't working because of workflow mismatch:

1. **Records created in**: PreInventory database/layout  
2. **PDFTimesheet script**: Processes PreInventory records (may delete them)
3. **Barcodes are on**: "Time Clock Reduced" layout (different table/layout)
4. **Timing issue**: We're trying to refresh barcodes before the main record exists

## Current Workflow Analysis

```
1. API creates record in PreInventory (Record ID: X)
2. PDFTimesheet script runs automatically 
3. PDFTimesheet may create record in main table
4. PDFTimesheet may delete PreInventory record  
5. Python tries to refresh barcodes on Record ID X (which may not exist anymore)
```

## Solutions to Try

### Option 1: Modify PDFTimesheet Script
Add barcode refresh steps to the existing PDFTimesheet script:

```
# At the end of PDFTimesheet script:
# After creating the main table record

# Force barcode refresh on the main table record  
Go to Layout ["Time Clock Reduced"]
Refresh Window [Flush cached join results; Flush cached SQL data]

# Update barcode containers
Set Field [BarcodeContainer_PO; Code128("" & Whittaker Shipper # & "")]
Set Field [BarcodeContainer_Part; Code39("" & Part Number & "")]
Set Field [BarcodeContainer_Qty; Code93("" & Quantity & "")]

Commit Records/Requests [No dialog]
```

### Option 2: Delay Barcode Refresh
Add a delay in Python before calling barcode refresh:

```python
# In filemaker_integration.py, after PDFTimesheet script
if script_error == '0':
    print("✅ PDFTimesheet script executed successfully")
    
    # Wait for PDFTimesheet to complete its work
    time.sleep(2)
    
    # Find the main table record by PO number instead of PreInventory record ID
    self.refresh_barcodes_by_po_number(po_number)
```

### Option 3: Use PO Number Instead of Record ID
Create a new method that finds records by PO number:

```python
def refresh_barcodes_by_po_number(self, po_number):
    """Find record by PO number and refresh barcodes"""
    if not self.token:
        return False
        
    # Find record in main table by PO number
    find_url = f"{self.server}/fmi/data/v1/databases/{self.database}/layouts/Time Clock Reduced/_find"
    find_request = {"query": [{"Whittaker Shipper #": str(po_number)}]}
    headers = {'Authorization': f'Bearer {self.token}', 'Content-Type': 'application/json'}
    
    try:
        response = requests.post(find_url, json=find_request, headers=headers, verify=False)
        if response.status_code == 200:
            records = response.json().get('response', {}).get('data', [])
            if records:
                main_record_id = records[0]['recordId']
                return self.refresh_barcodes(main_record_id)
    except Exception as e:
        print(f"❌ Error finding main record: {e}")
    
    return False
```

### Option 4: Simple Manual Approach
Since the automation is complex, you could:

1. **Skip automatic barcode refresh** in Python
2. **Manually refresh** in FileMaker after PDFs are generated
3. **Add layout trigger** to Time Clock Reduced that refreshes barcodes on record load

## Recommended Next Steps

1. **Check your workflow**: 
   - Does PDFTimesheet create records in a different table?
   - Are PreInventory records deleted after processing?
   - What table/layout actually contains the barcodes?

2. **Test manually**:
   - Create a test record in the main table
   - Run the RefreshBarcodes script manually
   - See if barcodes appear

3. **Simplify**:
   - Try Option 1 (modify PDFTimesheet) first
   - It's the most reliable approach

## Quick Debug Script

Run this in FileMaker to check your setup:

```
# Debug script to check barcode setup
Go to Layout ["Time Clock Reduced"]
New Record/Request
Set Field [Whittaker Shipper #; "TEST123"]
Set Field [Part Number; "PART123"] 
Set Field [Quantity; "10"]

# Test if barcode containers work
Set Field [BarcodeContainer_PO; Code128("TEST123")]
Set Field [BarcodeContainer_Part; Code39("PART123")]
Set Field [BarcodeContainer_Qty; Code93("10")]

Commit Records/Requests
# Check if barcodes appear
```

If this test works, then the issue is workflow/timing, not the plugin itself.
