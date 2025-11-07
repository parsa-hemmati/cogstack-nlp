#!/bin/bash
#
# Install Git hooks for CogStack NLP project
#

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Installing Git hooks...${NC}"
echo ""

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
HOOKS_SOURCE_DIR="$PROJECT_ROOT/.git-hooks"
HOOKS_TARGET_DIR="$PROJECT_ROOT/.git/hooks"

# Check if .git directory exists
if [ ! -d "$PROJECT_ROOT/.git" ]; then
    echo -e "${RED}Error: .git directory not found${NC}"
    echo "Are you running this from the repository root?"
    exit 1
fi

# Check if .git-hooks directory exists
if [ ! -d "$HOOKS_SOURCE_DIR" ]; then
    echo -e "${RED}Error: .git-hooks directory not found${NC}"
    exit 1
fi

# Create hooks directory if it doesn't exist
mkdir -p "$HOOKS_TARGET_DIR"

# Install pre-commit hook
if [ -f "$HOOKS_SOURCE_DIR/pre-commit" ]; then
    echo "Installing pre-commit hook..."

    # Check if hook already exists
    if [ -f "$HOOKS_TARGET_DIR/pre-commit" ]; then
        echo -e "${YELLOW}Warning: pre-commit hook already exists${NC}"
        read -p "Overwrite? (y/N) " -n 1 -r
        echo ""
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            echo "Skipping pre-commit hook"
        else
            cp "$HOOKS_SOURCE_DIR/pre-commit" "$HOOKS_TARGET_DIR/pre-commit"
            chmod +x "$HOOKS_TARGET_DIR/pre-commit"
            echo -e "${GREEN}✓ pre-commit hook installed${NC}"
        fi
    else
        cp "$HOOKS_SOURCE_DIR/pre-commit" "$HOOKS_TARGET_DIR/pre-commit"
        chmod +x "$HOOKS_TARGET_DIR/pre-commit"
        echo -e "${GREEN}✓ pre-commit hook installed${NC}"
    fi
else
    echo -e "${YELLOW}Warning: pre-commit hook source not found${NC}"
fi

echo ""
echo -e "${GREEN}Git hooks installation complete!${NC}"
echo ""
echo "Installed hooks:"
ls -l "$HOOKS_TARGET_DIR" | grep -E '^-.*x' | awk '{print "  - " $9}'
echo ""
echo "To test the pre-commit hook:"
echo "  1. Make a code change"
echo "  2. Try to commit without updating CONTEXT.md"
echo "  3. Hook should prevent commit"
echo ""
echo "To bypass hook (emergency only):"
echo "  git commit --no-verify"
echo ""
