# 🎯 Parker PO OCR Chat Files Guide

Your project now has a comprehensive set of specialized chat prompts to help maintain focus, consistency, and efficiency throughout development. Here's your complete guide:

## 📋 Available Chat Prompts

### 🎯 **Project Management**
- **`project-status.prompt.md`** - Use for project reviews, progress tracking, and priority planning
  - *When to use*: Weekly reviews, milestone planning, priority assessment
  - *Focus*: Current status, next steps, risk assessment, resource allocation

### 🛠️ **Development & Technical**

#### **`development.prompt.md`** - General development guidance
- *When to use*: Starting new features, general troubleshooting, architecture decisions
- *Focus*: System overview, development environment, best practices

#### **`dashboard.prompt.md`** - Frontend/UI development
- *When to use*: Working on Flask app, Bootstrap UI, JavaScript issues, modal problems
- *Focus*: Dashboard templates, Bootstrap dark theme, JavaScript debugging

#### **`filemaker.prompt.md`** - Database integration
- *When to use*: FileMaker API issues, record management, authentication problems
- *Focus*: Data API, duplicate records, field mapping, error handling

#### **`docker.prompt.md`** - Container management
- *When to use*: Deployment issues, container problems, performance optimization
- *Focus*: Container operations, docker-compose, deployment workflows

### 🔧 **Workflow & Operations**

#### **`troubleshooting.prompt.md`** - Systematic problem solving
- *When to use*: When things break, systematic debugging needed
- *Focus*: Diagnostic procedures, step-by-step troubleshooting, emergency procedures

#### **`git-workflow.prompt.md`** - Version control guidance
- *When to use*: Git questions, branch management, collaboration workflows
- *Focus*: Branch strategy, commit practices, merge procedures

## 🚀 How to Use These Prompts

### **Quick Selection Guide:**

```
❓ "What should I work on next?" → project-status.prompt.md
🐛 "Something is broken" → troubleshooting.prompt.md  
🎨 "Dashboard/UI issue" → dashboard.prompt.md
🗄️ "FileMaker problem" → filemaker.prompt.md
🐳 "Container won't start" → docker.prompt.md
📝 "Git question" → git-workflow.prompt.md
⚡ "General development" → development.prompt.md
```

### **Session Workflow:**

1. **Start your session**: Choose the most relevant prompt for your current task
2. **Load context**: The prompt will provide specific project context and background
3. **Get guidance**: Follow the structured approaches and use provided tools
4. **Stay focused**: The prompt keeps the conversation centered on your specific need
5. **Document**: Update project status or create issues for future tracking

## 🎯 Prompt-Specific Quick Start

### Working on Dashboard Issues
```
1. Load: dashboard.prompt.md
2. Check: Browser console for JavaScript errors
3. Test: Using dashboard-restart and dashboard-logs
4. Debug: Bootstrap tabs, modal functionality, AJAX calls
```

### FileMaker Integration Problems
```
1. Load: filemaker.prompt.md
2. Test: Using test_filemaker_connection.py
3. Debug: Authentication, duplicate records, field mapping
4. Verify: Using debug.sh filemaker
```

### Project Planning Session
```
1. Load: project-status.prompt.md
2. Review: Current milestones and completed work
3. Assess: Risks, priorities, and resource needs
4. Plan: Next sprint and long-term roadmap
```

### System Troubleshooting
```
1. Load: troubleshooting.prompt.md
2. Follow: Systematic diagnostic approach
3. Use: Built-in debug scripts (debug.sh, dashboard-logs)
4. Document: Solutions for future reference
```

## 📊 Integration with Development Tools

Each prompt integrates with your existing development environment:

- **Development Scripts**: `dev-environment.sh`, `debug.sh`, `hot-reload.sh`
- **Git Workflow**: Existing aliases and branch strategy
- **Container Management**: Docker compose and deployment scripts
- **Monitoring**: Log analysis and system diagnostics

## 💡 Best Practices

1. **Choose the right prompt** - Select based on your immediate need
2. **Follow the structure** - Each prompt provides systematic approaches
3. **Use provided tools** - Leverage existing development scripts and shortcuts
4. **Document solutions** - Keep the project knowledge base updated
5. **Stay consistent** - Follow the established patterns and conventions

## 🔄 Maintaining the Prompts

These prompts are living documents. Update them as:
- Project requirements evolve
- New tools are added
- Common issues are identified
- Best practices are refined

Your Parker PO OCR project now has professional-grade project management and development guidance built right in! 🎉
