# Git Development Workflow

This document describes the Git workflow and development practices for the Parker PO OCR System.

## Repository Structure

```
ParkerPOsOCR/
├── .git/                   # Git repository data
├── .gitignore             # Excluded files and patterns
├── README.md              # Project documentation
├── setup-git.sh           # Git configuration script
├── dev-environment.sh     # Development environment setup
├── dashboard/             # Web dashboard application
├── docker_system/         # Docker containerization
├── POs/                   # Processed purchase orders (samples only)
├── Archive/               # Archived processed files
└── development scripts/   # Various utility scripts
```

## Branches

- **main**: Production-ready code, stable releases
- **development**: Active development, feature integration

## Development Workflow

### Initial Setup
```bash
# Run once after cloning
sh setup-git.sh
source dev-environment.sh
```

### Daily Development
```bash
# Start development
git dev-start              # Switch to development branch
git dev-sync              # Sync with main if needed

# Make changes...
git st                    # Check status
git add .                 # Stage changes
git ci -m "Description"   # Commit changes

# When ready to deploy
git dev-push              # Merge to main
```

### Quick Commands
```bash
git st           # Short status
git logs         # Recent commits
git tree         # Visual commit tree
git last         # Last commit details
```

## File Management

### Included in Version Control
- Source code (.py, .html, .js, .css)
- Configuration templates (.env.development)
- Documentation (.md files)
- Docker configurations
- Sample PO data for testing

### Excluded from Version Control
- Log files (*.log)
- SSL certificates (*.crt, *.key)
- Environment files with secrets (.env, filemaker_config.json)
- Large processed data (Archive/, processed POs/)
- Python cache (__pycache__/)

## Development Environment

The `dev-environment.sh` script provides shortcuts for:
- Container management (dashboard-restart, dashboard-rebuild)
- Log viewing (dashboard-logs, system-logs)
- Debugging (debug-network, debug-files)
- Hot-reload development

## Best Practices

1. **Always work on development branch for new features**
2. **Commit frequently with descriptive messages**
3. **Test thoroughly before merging to main**
4. **Keep sensitive configuration out of version control**
5. **Use provided development scripts for consistency**

## Deployment

Production deployment should always be from the `main` branch:
```bash
git co main               # Switch to main
git pull                 # Get latest changes
./deploy_dashboard_changes.sh  # Deploy
```

## Troubleshooting

### Common Issues
- **Merge conflicts**: Use `git status` to see conflicted files
- **Unstaging files**: Use `git unstage <filename>`
- **Viewing changes**: Use `git st` for overview, `git tree` for history

### Getting Help
```bash
git --help               # General Git help
git <command> --help     # Specific command help
```

## Integration with Development Scripts

The Git workflow integrates with existing development tools:
- `debug.sh` - System diagnostics
- `hot-reload.sh` - Automatic reloading
- `deploy_dashboard_changes.sh` - Deployment
- `dev-environment.sh` - Development shortcuts

This creates a complete development ecosystem for efficient Parker PO OCR System development.
