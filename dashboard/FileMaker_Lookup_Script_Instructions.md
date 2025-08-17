# FileMaker "Lookup" Script Instructions - UPDATED FOR PART NUMBER LOOKUPS

Based on your FileMaker relationship diagram, the Description, Revision, and Op Sheet Issue fields are looked up from the PRICES 7-9-2002 table based on Part Number.

## Script: "Lookup" (UPDATED VERSION)

```filemaker
# Get the parameters passed from the API (PO Number|Part Number)
Set Variable [ $params ; Get ( ScriptParameter ) ]
Set Variable [ $poNumber ; GetValue ( Substitute ( $params ; "|" ; ¶ ) ; 1 ) ]
Set Variable [ $partNumber ; GetValue ( Substitute ( $params ; "|" ; ¶ ) ; 2 ) ]

# Go to the correct layout
Go to Layout [ "PreInventory" (PreInventory) ]

# Find the record that was just created using PO number
Enter Find Mode [ Pause: Off ]
Set Field [ Whittaker Shipper # ; $poNumber ]
Perform Find

# CRITICAL: Force relookup on Part Number field first (this triggers Description, Revision, Op Sheet Issue)
Relookup Field Contents [ No dialog ; PART NUMBER ]

# Wait a moment for FileMaker to process
Pause/Resume Script [ Duration (seconds): 0.5 ]

# Now force relookup on the fields that depend on Part Number
Relookup Field Contents [ No dialog ; Description ]
Relookup Field Contents [ No dialog ; Revision ]
Relookup Field Contents [ No dialog ; Op Sheet Issue ]

# Also relookup Planner Name if it's a lookup field
Relookup Field Contents [ No dialog ; Planner Name ]

# Alternative method: Set the Part Number field to itself to trigger lookups
Set Field [ PART NUMBER ; PART NUMBER ]

# Commit the changes
Commit Records/Requests [ No dialog ]

# Return success with details
Exit Script [ Text Result: "Lookups completed: Part=" & $partNumber & " PO=" & $poNumber ]
```

## Alternative Script (if the above doesn't work):

```filemaker
# Get parameters
Set Variable [ $params ; Get ( ScriptParameter ) ]
Set Variable [ $poNumber ; GetValue ( Substitute ( $params ; "|" ; ¶ ) ; 1 ) ]
Set Variable [ $partNumber ; GetValue ( Substitute ( $params ; "|" ; ¶ ) ; 2 ) ]

# Go to layout
Go to Layout [ "PreInventory" (PreInventory) ]

# Find the record
Enter Find Mode [ Pause: Off ]
Set Field [ Whittaker Shipper # ; $poNumber ]
Perform Find

# Method 1: Clear and reset the Part Number to force lookup
Set Field [ PART NUMBER ; "" ]
Commit Records/Requests [ No dialog ]
Set Field [ PART NUMBER ; $partNumber ]
Commit Records/Requests [ No dialog ]

# Method 2: Use Relookup on all related fields
Relookup Field Contents [ No dialog ; PART NUMBER ]
Relookup Field Contents [ No dialog ; Description ]
Relookup Field Contents [ No dialog ; Revision ]
Relookup Field Contents [ No dialog ; Op Sheet Issue ]

Exit Script [ Text Result: "Part number lookups forced" ]
```

## What the API now sends:
- Parameter format: "4551241597|450130*OP40"
- First part: PO Number (to find the record)
- Second part: Part Number (to verify the lookup value)

## Key Points:
1. **Part Number is the lookup key** for Description, Revision, Op Sheet Issue
2. **Script gets both PO and Part Number** from the API parameter
3. **Forces relookup on Part Number field first** to trigger related lookups
4. **Backup method clears and resets Part Number** to force lookup evaluation

## Testing Steps:
1. Update your "Lookup" script with the code above
2. Test manually: Run script with parameter "4551241597|450130*OP40"
3. Verify Description, Revision, Op Sheet Issue fields populate
4. Test via dashboard API integration
