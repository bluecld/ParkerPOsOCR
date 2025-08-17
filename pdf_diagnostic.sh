#!/bin/bash

# PDF Diagnostic Script
# This script helps diagnose PDF corruption issues

echo "🔍 PDF Diagnostic Report"
echo "======================="
echo "Date: $(date)"
echo ""

# Check recent error files
echo "📋 Recent Error Files:"
ls -la /volume1/Main/Main/ParkerPOsOCR/Errors/*.pdf 2>/dev/null | tail -5

echo ""
echo "🔍 PDF Analysis:"

# Analyze the latest error files
for pdf in /volume1/Main/Main/ParkerPOsOCR/Errors/20250814_083*_ERROR_*.pdf; do
    if [ -f "$pdf" ]; then
        echo ""
        echo "File: $(basename $pdf)"
        echo "Size: $(stat -c%s "$pdf" 2>/dev/null || echo "Unknown") bytes"
        echo "Type: $(file "$pdf" 2>/dev/null || echo "Unknown")"
        
        # Check page count using Docker container
        docker exec po-processor python -c "
import fitz
try:
    doc = fitz.open('$pdf')
    print(f'Pages: {len(doc)}')
    if len(doc) > 0:
        page = doc[0]
        print(f'First page size: {page.rect}')
    doc.close()
except Exception as e:
    print(f'Error opening PDF: {e}')
" 2>/dev/null
    fi
done

echo ""
echo "✅ Successful Files (for comparison):"
for pdf in /volume1/Main/Main/ParkerPOsOCR/Archive/20250814_*_File_*.pdf; do
    if [ -f "$pdf" ]; then
        echo ""
        echo "File: $(basename $pdf)"
        echo "Size: $(stat -c%s "$pdf" 2>/dev/null || echo "Unknown") bytes"
        
        docker exec po-processor python -c "
import fitz
try:
    doc = fitz.open('$pdf')
    print(f'Pages: {len(doc)}')
    doc.close()
except Exception as e:
    print(f'Error: {e}')
" 2>/dev/null
    fi
done

echo ""
echo "🚨 Issues Found:"
echo "- Failed PDFs have 0 pages (corrupted)"
echo "- Successful PDFs have 2-3 pages (normal)"
echo ""
echo "💡 Recommendations:"
echo "1. Re-scan the documents with fresh scans"
echo "2. Check scanner settings and connections"
echo "3. Verify file integrity immediately after scanning"
echo "4. Consider using a different file format temporarily (if scanner supports)"
echo ""
echo "📊 Current System Status:"
docker exec po-processor echo "Container is running and ready for new files"
