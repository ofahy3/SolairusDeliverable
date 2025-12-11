# AGENTS-TEMPLATE.md - Python Project Quality Template

> Reusable template for AI coding agents. Copy to new projects and customize.

## How to Use This Template

1. Copy this file to your project root as `AGENTS.md`
2. Replace `{{PROJECT_NAME}}` with your project name
3. Replace `{{PACKAGE_NAME}}` with your Python package name
4. Customize the Client Context section for your project
5. Update the Architecture section to match your project structure

---

## Project Overview

{{PROJECT_NAME}} - Brief description of what this project does.

---

## Client Context

**Primary Contact**: [Name and Role]
**Their workflow**: [What they do with your output]

### What they specifically asked for:
- [Key requirement 1]
- [Key requirement 2]

### What they do NOT want:
- [Anti-requirement 1]
- [Anti-requirement 2]

---

## Dev Environment

```bash
# Install dependencies
pip install -e ".[dev]"

# Environment variables (create .env file)
API_KEY=...
```

## Testing

```bash
# Run tests (context-efficient)
~/.claude/hooks/run-silent python3 -m pytest tests/

# Type checking
~/.claude/hooks/run-silent python3 -m mypy {{PACKAGE_NAME}} --ignore-missing-imports
```

**Coverage target:** 70%+

## Code Style

- **Type hints required** - All functions must have type annotations
- **Mypy clean** - Zero mypy errors allowed
- **No unused imports** - Use `pyflakes` to check
- **Minimal public API** - Hide complexity behind simple interfaces

## Architecture

```
{{PACKAGE_NAME}}/
├── api.py              # Public API
├── core/               # Core logic
├── clients/            # External API clients
├── config/             # Configuration (inside package!)
├── utils/              # Utilities
└── web/                # Web interface (if applicable)
```

---

## Code Quality Playbook

### Before Starting Work: Quality Assessment

Run this checklist before writing new code or when onboarding to a codebase:

**1. Import Hygiene (P0 - Blocking)**
- [ ] All imports use proper module paths (not relative to PYTHONPATH)
- [ ] No `from config.xxx` without package prefix
- Verify: `grep -r "from config\." --include="*.py" . | grep -v .venv`

**2. Dead Code Detection (P1)**
- [ ] No unused classes or methods
- [ ] No commented-out code blocks
- [ ] No backwards-compatibility shims for removed features
- Verify: `python3 -m pyflakes {{PACKAGE_NAME}}/`

**3. Config Organization (P2)**
- [ ] Single config location (inside package: `{{PACKAGE_NAME}}/config/`)
- [ ] No split config directories at root level
- Verify: `find . -maxdepth 1 -type d -name "config"`

**4. Module Exports (P3 - Blocking)**
- [ ] All `__init__.py` files have explicit exports or docstrings
- [ ] No empty `__init__.py` files (except for namespace packages)
- Verify: `find . -name "__init__.py" -empty -not -path "./.venv/*"`

**5. File Size Limits (P4)**
- [ ] No file exceeds 700 lines
- [ ] Large files split by responsibility
- Verify: `find . -name "*.py" -not -path "./.venv/*" -exec wc -l {} \; | sort -rn | head -10`

**6. API Simplicity**
- [ ] Public API is minimal (< 5 lines to success)
- [ ] Compare to Stripe: `stripe.Charge.create(...)` = 3 lines
- Document: "Lines to success" metric

### Priority Framework for Fixes

| Priority | Type | Examples | Fix When |
|----------|------|----------|----------|
| P0 | Breaking | Broken imports, won't install | Immediately |
| P1 | Dead code | Unused classes, methods | Same session |
| P2 | Organization | Split configs, scattered logic | Same session |
| P3 | Hygiene | Empty `__init__.py`, missing exports | Same session |
| P4 | Optional | Large files, consolidation | If time permits |

### Verification Protocol

After any refactoring:
1. `~/.claude/hooks/run-silent python3 -m pytest tests/` - All tests pass
2. `wc -l <changed_files>` - Verify size reduction
3. `grep -r "<old_pattern>" . | grep -v .venv` - Confirm old pattern removed
4. Update todo list with completion status

### Quality Gate: Would Google Hire This Code?

Before declaring work complete, answer:
- [ ] Would a Google engineer recognize this as professional?
- [ ] Is it as elegant as Stripe's 7-line API?
- [ ] Are there any broken paths or dead files?
- [ ] Is the test suite comprehensive (70%+ coverage)?

If any answer is "no", continue improving.

### Automated Quality Gate

Create `scripts/quality-check.sh`:
```bash
#!/bin/bash
set -e
echo "Running Quality Gate..."

# P0: Import hygiene
if grep -r "from config\." --include="*.py" . 2>/dev/null | grep -v ".venv" | grep -v __pycache__; then
    echo "FAIL: Broken imports found"
    exit 1
fi

# P2: Config at root level
if [ -d "./config" ]; then
    echo "FAIL: Config directory at root level"
    exit 1
fi

# P3: Empty __init__.py
if find . -name "__init__.py" -not -path "./.venv/*" -empty | grep .; then
    echo "FAIL: Empty __init__.py files found"
    exit 1
fi

# P4: File size warnings
find . -name "*.py" -not -path "./.venv/*" -exec wc -l {} \; | awk '$1 > 700 {print "WARN: Large file:", $0}'

# Tests
python3 -m pytest tests/ -q

echo "Quality Gate Passed"
```

---

## PR Guidelines

**Commit message format:**
```
<type>: <description>

<body>

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>
```

**Types:** fix, feat, refactor, docs, test, chore

## Anti-Patterns to Avoid

1. **Dead code** - Delete unused classes, methods, parameters
2. **Facade bloat** - Don't create wrapper files that just re-export
3. **Unused imports** - Remove them immediately
4. **Bare except** - Always specify exception types
5. **f-strings without placeholders** - Use regular strings instead
6. **Over-engineering** - Minimal code that solves the problem
7. **Split configs** - Keep config inside the package
8. **Empty `__init__.py`** - Add exports or docstrings

## Security

- Never commit `.env` or API keys
- Validate all external input
- Use parameterized queries for databases
