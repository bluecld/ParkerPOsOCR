#!/bin/bash
# Git Development Helpers for ParkerPO OCR Project

# Set up useful git aliases
git config alias.st "status --short"
git config alias.co "checkout"
git config alias.br "branch"
git config alias.ci "commit"
git config alias.ca "commit -a"
git config alias.unstage "reset HEAD --"
git config alias.last "log -1 HEAD"
git config alias.visual "!gitk"
git config alias.tree "log --oneline --decorate --graph --all"
git config alias.logs "log --oneline --decorate --graph -10"

# Development workflow aliases
git config alias.dev-start "checkout development"
git config alias.dev-sync "!git checkout development && git merge main"
git config alias.dev-push "!git checkout main && git merge development && git push"

echo "✅ Git aliases configured!"
echo ""
echo "Available aliases:"
echo "  git st         - Short status"
echo "  git co         - Checkout"
echo "  git br         - Branch"
echo "  git ci         - Commit"
echo "  git ca         - Commit all"
echo "  git unstage    - Unstage files"
echo "  git last       - Show last commit"
echo "  git tree       - Pretty log tree"
echo "  git logs       - Last 10 commits"
echo "  git dev-start  - Switch to development"
echo "  git dev-sync   - Sync development with main"
echo "  git dev-push   - Merge development to main and push"
echo ""
echo "Current branches:"
git branch -a
echo ""
echo "Repository status:"
git status --short || git status
