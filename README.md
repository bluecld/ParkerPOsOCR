# 📋 Parker PO OCR System - Quick Reference

## 🎯 System Summary
**Status:** ✅ **OPERATIONAL** (Issues Fixed: August 13, 2025)  
**Purpose:** Automated PO processing with OCR text extraction  
**Container:** `po-processor` running on Docker  

## 🚀 Essential Commands

### Quick Start/Stop
```bash
# Navigate to project
cd /volume1/Main/Main/ParkerPOsOCR

# Simple commands
./simple_restart.sh start     # Start system
./simple_restart.sh stop      # Stop system  
./simple_restart.sh restart   # Quick restart
./simple_restart.sh status    # Check status
./simple_restart.sh logs      # View logs
./simple_restart.sh rebuild   # Rebuild container
```

### Manual Docker Commands
```bash
cd /volume1/Main/Main/ParkerPOsOCR/docker_system
docker-compose up -d          # Start
docker-compose down           # Stop
docker-compose logs -f        # View logs
docker ps                     # Check status
```

## 📁 File Processing Workflow

1. **Input:** Place PDFs in `/volume1/Main/Main/ParkerPOsOCR/Scans/`
2. **Processing:** System automatically detects and processes (2-second delay)
3. **Success:** Results appear in `/volume1/Main/Main/ParkerPOsOCR/POs/`
4. **Errors:** Failed files moved to `/volume1/Main/Main/ParkerPOsOCR/Errors/`
5. **Archive:** Completed files moved to `/volume1/Main/Main/ParkerPOsOCR/Archive/`

## 🔧 Key Files

| File | Purpose |
|------|---------|
| `PROJECT_SUMMARY.md` | Complete project documentation |
| `INSTRUCTIONS.md` | Detailed usage instructions |
| `simple_restart.sh` | Simple container control script |
| `restart_po_system.sh` | Advanced container management |
| `docker_system/docker-compose.yml` | Container configuration |
| `docker_system/scripts/ocr_pdf_searchable.py` | Fixed OCR processing |

## 🚨 Recent Fixes (August 13, 2025)

### Problem Solved
- **Issue:** OCR was failing with "cannot save with zero pages" error
- **Cause:** Tesseract path configured for Windows, zero-page handling bug
- **Fix:** Updated for Linux paths, added graceful fallback handling

### Files Modified
- `ocr_pdf_searchable.py` - Fixed Tesseract path detection and zero-page bug

## 📊 Health Monitoring

### Check System Health
```bash
./simple_restart.sh status                    # Container status
tail -f /volume1/Main/Main/ParkerPOsOCR/POs/po_processor.log  # Processing log
docker stats po-processor                     # Resource usage
```

### Processing Test
```bash
# 1. Ensure system is running
./simple_restart.sh status

# 2. Place a test PDF in Scans folder
cp "test.pdf" /volume1/Main/Main/ParkerPOsOCR/Scans/

# 3. Watch processing logs
./simple_restart.sh logs
```

## 🆘 Troubleshooting

| Problem | Solution |
|---------|----------|
| Container won't start | `./simple_restart.sh rebuild` |
| Files not processing | Check logs: `./simple_restart.sh logs` |
| High memory usage | `./simple_restart.sh restart` |
| OCR errors | Files should now process (issue fixed) |
| Permission errors | Check folder permissions |

## 📈 Performance Expectations

- **Processing Time:** 20-30 seconds per PDF
- **Memory Usage:** ~200MB per container
- **File Detection:** 2-second delay after file placement
- **OCR Success Rate:** Significantly improved after fix

## 🔮 Future Enhancements

- [ ] FileMaker database integration
- [ ] Web dashboard for monitoring  
- [ ] Email notifications
- [ ] Batch processing capabilities

---

**Quick Help:** Run `./simple_restart.sh` with no arguments to see usage options  
**Full Documentation:** See `PROJECT_SUMMARY.md` and `INSTRUCTIONS.md`  
**Last Updated:** August 13, 2025
