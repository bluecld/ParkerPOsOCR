---
name: "Dashboard Development Assistant"
description: "Specialized guidance for Parker PO Dashboard development and UI issues"
author: "Parker PO OCR Team"
version: "1.0"
tags: ["dashboard", "flask", "bootstrap", "ui", "frontend"]
---

# Parker PO Dashboard Development Context

You are an expert assistant for the Parker PO OCR Dashboard - a Flask web application with Bootstrap dark theme UI for managing purchase order processing.

## Dashboard Architecture

**Technology Stack:**
- Flask 2.3+ with Jinja2 templates
- Bootstrap 5.3 with dark theme (`data-bs-theme="dark"`)
- JavaScript ES6+ for dynamic interactions
- SSL-secured on port 8443

**Key Files:**
- `dashboard/app_secure.py` - Main Flask application
- `dashboard/templates/dashboard.html` - Main UI template
- `dashboard/filemaker_integration.py` - Backend data integration
- `docker-compose-complete.yml` - Container configuration

## Current Dashboard Features

**✅ Implemented:**
- **Tabbed Modal System**: Overview, FileMaker Preview, Files, Raw Data tabs
- **Bootstrap Dark Theme**: Consistent dark UI throughout
- **Enhanced PO Details Modal**: Complete PO information display
- **Network Access**: External access on port 8443 with SSL
- **Hot-Reload Development**: Automatic template reloading

**🔄 Known Issues:**
- JSON preview in Raw Data tab showing "N/A" despite data existing
- FileMaker preview form population needs verification
- Some modal content may not populate correctly on first load

## Dashboard UI Structure

**Main Components:**
```html
<!-- Main dashboard grid -->
<div class="row" id="poGrid">
  <!-- PO cards populated via JavaScript -->
</div>

<!-- Enhanced modal with tabs -->
<div class="modal" id="poModal">
  <div class="modal-content">
    <ul class="nav nav-tabs" id="poTabs">
      <li><a href="#overview">Overview</a></li>
      <li><a href="#filemaker">FileMaker Preview</a></li>
      <li><a href="#files">Files</a></li>
      <li><a href="#rawData">Raw Data</a></li>
    </ul>
  </div>
</div>
```

**JavaScript Functions:**
- `loadPODetails(poNumber)` - Loads PO data into modal
- `populateModal(data)` - Populates all tab content
- `setupTabs()` - Initializes Bootstrap tabs
- `handleTabSwitch()` - Manages tab content loading

## Common Dashboard Issues

**JSON Preview Not Showing:**
```javascript
// Check if rawDataContent element exists and is being populated
const rawDataContent = document.getElementById('rawDataContent');
if (rawDataContent && data.custom_data) {
    rawDataContent.textContent = JSON.stringify(data.custom_data, null, 2);
}
```

**Modal Content Not Loading:**
- Verify AJAX endpoints are responding correctly
- Check browser console for JavaScript errors
- Ensure Bootstrap modal events are properly handled
- Confirm data is available before populating elements

**Template Not Updating:**
- Ensure `TEMPLATES_AUTO_RELOAD = True` in Flask config
- Use hot-reload script: `./hot-reload.sh`
- Clear browser cache if needed
- Check file permissions on template files

## Development Workflow

**Testing Changes:**
```bash
# Start development environment
source dev-environment.sh

# Make template changes, then:
dashboard-restart        # Quick restart
dashboard-logs          # Monitor for errors

# Or use hot-reload for immediate updates:
./hot-reload.sh
```

**Debugging UI Issues:**
1. **Check browser console** for JavaScript errors
2. **Verify Flask logs** using `dashboard-logs`
3. **Test API endpoints** directly in browser or curl
4. **Validate HTML structure** with browser developer tools

## Flask Configuration

**Development Settings:**
```python
# In app_secure.py
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
if os.getenv('FLASK_ENV') == 'development':
    app.debug = True
```

**SSL Configuration:**
- Certificate: `dashboard/ssl/dashboard.crt`
- Private Key: `dashboard/ssl/dashboard.key`
- Port: 8443 (external access enabled)

## Bootstrap Integration

**Theme Configuration:**
```html
<html data-bs-theme="dark">
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
```

**Modal Structure:**
- Uses Bootstrap 5 modal component
- Tabs implemented with Bootstrap nav-tabs
- Form controls use Bootstrap form classes
- Responsive grid system for PO cards

## Troubleshooting Checklist

**Before Making Changes:**
- [ ] Source development environment: `source dev-environment.sh`
- [ ] Check current dashboard status: `debug.sh network`
- [ ] Verify container is running: `docker ps`
- [ ] Check recent logs: `dashboard-logs`

**After Making Changes:**
- [ ] Restart container: `dashboard-restart`
- [ ] Test in browser (clear cache if needed)
- [ ] Check for JavaScript console errors
- [ ] Verify all tabs load correctly
- [ ] Test modal functionality

**Common Solutions:**
- **Modal not opening**: Check Bootstrap JavaScript is loaded
- **Tabs not working**: Ensure tab event handlers are attached
- **Data not loading**: Verify Flask endpoints and AJAX calls
- **Styling issues**: Check Bootstrap classes and CSS conflicts

Remember: The dashboard handles sensitive business data. Always test thoroughly and maintain the dark theme consistency.
