#!/bin/bash
#
# Install git hooks from .git-hooks/ directory
#
# This script copies all hooks to .git/hooks/ and makes them executable
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get script directory and repository root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

echo -e "${YELLOW}Installing git hooks...${NC}"
echo ""

# Check if .git directory exists
if [ ! -d "$REPO_ROOT/.git" ]; then
    echo -e "${RED}Error: .git directory not found${NC}"
    echo "Are you in the repository root?"
    exit 1
fi

# Check if .git-hooks directory exists
if [ ! -d "$REPO_ROOT/.git-hooks" ]; then
    echo -e "${RED}Error: .git-hooks directory not found${NC}"
    exit 1
fi

# Create .git/hooks directory if it doesn't exist
mkdir -p "$REPO_ROOT/.git/hooks"

# Install each hook
HOOKS_INSTALLED=0
HOOKS_FAILED=0

for hook in "$REPO_ROOT/.git-hooks"/*; do
    # Skip README.md
    if [[ "$(basename "$hook")" == "README.md" ]]; then
        continue
    fi

    # Skip if not a file
    if [ ! -f "$hook" ]; then
        continue
    fi

    HOOK_NAME=$(basename "$hook")
    TARGET="$REPO_ROOT/.git/hooks/$HOOK_NAME"

    # Copy hook
    if cp "$hook" "$TARGET"; then
        chmod +x "$TARGET"
        echo -e "${GREEN}✓${NC} Installed: $HOOK_NAME"
        ((HOOKS_INSTALLED++))
    else
        echo -e "${RED}✗${NC} Failed: $HOOK_NAME"
        ((HOOKS_FAILED++))
    fi
done

echo ""
echo "Summary:"
echo "  Installed: $HOOKS_INSTALLED hook(s)"
if [ "$HOOKS_FAILED" -gt 0 ]; then
    echo -e "  ${RED}Failed: $HOOKS_FAILED hook(s)${NC}"
fi

echo ""
echo -e "${GREEN}Git hooks installation complete!${NC}"
echo ""
echo "Hooks installed:"
echo "  - pre-commit: Enforces CONTEXT.md updates"
echo "  - commit-msg: Validates commit message format"
echo "  - prepare-commit-msg: Provides commit message template"
echo ""
echo "See .git-hooks/README.md for details."
echo ""

exit 0
