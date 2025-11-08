# Git Hooks

This directory contains Git hooks to enforce project standards and quality.

## Available Hooks

### 1. Pre-Commit Hook

**Purpose**: Ensures CONTEXT.md is updated with every code change

**What it checks**:
- ✅ CONTEXT.md is modified when code changes are committed
- ✅ CONTEXT.md has meaningful changes (not just date update)
- ⚠️ Warns about console.log/debugger statements in JavaScript/TypeScript
- ⚠️ Warns about TODO comments without associated tasks

### 2. Commit-Msg Hook

**Purpose**: Enforces conventional commit message format

**What it checks**:
- ✅ First line follows `<type>(<scope>): <summary>` format
- ✅ Valid type (feat, fix, docs, style, refactor, test, chore, perf, security)
- ✅ Summary ≤72 characters (warns at >50 characters)
- ⚠️ Warns if body is missing for non-trivial commits
- ⚠️ Warns if CONTEXT.md Updates section missing for code changes

### 3. Prepare-Commit-Msg Hook

**Purpose**: Provides commit message template automatically

**What it does**:
- Inserts commit message template when message is empty
- Suggests scope based on branch name
- Includes examples and valid types
- Provides structured format for Changes, Rationale, Tests, CONTEXT.md Updates

## Installation

### Option 1: Automatic (Recommended)

```bash
# From repository root
./scripts/install-git-hooks.sh
```

### Option 2: Manual

```bash
# From repository root
cp .git-hooks/pre-commit .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit
```

### Option 3: Symbolic Link (Advanced)

```bash
# From repository root
ln -s ../../.git-hooks/pre-commit .git/hooks/pre-commit
```

**Benefits of symlink**: Hooks update automatically when pulled from git

## Verification

Test the hook:

```bash
# Try to commit code without updating CONTEXT.md
echo "console.log('test')" > test.js
git add test.js
git commit -m "test"
# Should fail with error about CONTEXT.md

# Clean up
rm test.js
```

## Bypassing the Hook (NOT RECOMMENDED)

If you absolutely must bypass (emergency hotfix only):

```bash
git commit --no-verify
```

**Warning**: Bypassing loses the context tracking benefit. Use only for:
- Emergency production hotfixes
- Reverting broken commits
- Fixing broken CI/CD

## Customization

To modify hook behavior, edit `.git-hooks/pre-commit` and reinstall.

## Troubleshooting

### Hook not running

**Problem**: Commits succeed without CONTEXT.md update

**Solutions**:
1. Check if hook is installed: `ls -la .git/hooks/pre-commit`
2. Check if hook is executable: `chmod +x .git/hooks/pre-commit`
3. Reinstall using installation steps above

### Hook failing incorrectly

**Problem**: Hook blocks legitimate commits

**Solutions**:
1. Verify CONTEXT.md is actually modified: `git diff --cached CONTEXT.md`
2. Ensure meaningful changes (not just date update)
3. Check if you're committing code vs documentation (hook only enforces for code)

### False positives on documentation

**Problem**: Hook requires CONTEXT.md for documentation changes

**Solution**: Hook should skip documentation-only commits. If not:
- Check file extensions in hook script
- Files in `docs/`, `.specify/`, and `*.md` should be exempt

## CI/CD Integration

The pre-commit hook is also enforced in CI/CD:

```yaml
# .github/workflows/ci.yml
- name: Check CONTEXT.md updated
  run: |
    if git diff --name-only ${{ github.event.before }}..${{ github.sha }} | grep -v 'CONTEXT.md' | grep -v '\.md$' | grep -v '^docs/' | grep -v '^\.specify/'; then
      if ! git diff --name-only ${{ github.event.before }}..${{ github.sha }} | grep 'CONTEXT.md'; then
        echo "Error: Code changes without CONTEXT.md update"
        exit 1
      fi
    fi
```

## Best Practices

**DO**:
- Update CONTEXT.md with every code commit
- Add meaningful context (ADRs, design decisions, rationale)
- Update "Recent Changes" section with each commit
- Document technical debt when taking shortcuts

**DON'T**:
- Use `--no-verify` routinely
- Update only the date in CONTEXT.md (hook will catch this)
- Skip CONTEXT.md updates thinking "I'll do it later"
- Commit code without proper context documentation

## Questions?

See [CONTEXT.md](../CONTEXT.md) for what to update.
See [CLAUDE.md](../CLAUDE.md) for full development guidelines.
