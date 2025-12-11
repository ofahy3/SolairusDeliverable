# AGENTS.md - Grainger MRO Intelligence Report Generator

> Configuration for AI coding agents working on this project.

## Project Overview

MRO Intelligence Report Generator for Grainger - generates biweekly geopolitical/economic intelligence reports by aggregating data from ErgoMind, GTA (Global Trade Alert), and FRED (Federal Reserve Economic Data). Translates global events into MRO market implications for Grainger's customer segments.

---

## Grainger Client Context

**Primary Contact**: Jenna Anderson (VP of Strategy, Analytics, and Technology Finance)
**Her workflow**: Sends weekly insights newsletter to DG (CEO) and Nancy (CLO)
**Renewal date**: March 2026

### What Jenna specifically asked for:
- "What's happening with tariffs that would impact the MRO market?"
- "What are outlooks for the US MRO market?"
- "What we think will happen to the price of steel - does that slow or grow the MRO market?"
- "How much price should we be passing through?" (pricing guidance)

### Grainger's Customer Segments:
- **Manufacturing**: Industrial/factory customers (largest segment)
- **Government**: Federal, state, military ($2B+ revenue, $400M military)
- **Commercial Facilities**: Office buildings, retail, hospitality, healthcare
- **Contractors**: Construction, electrical, plumbing, HVAC contractors

### What Grainger does NOT want:
- Generic geopolitical commentary without MRO implications
- International focus beyond USMCA
- Long-term forecasts (>6 months)
- Sectors outside their customer base

### Grainger's supply chain exposure:
- **20% of COGS from China** (tariff sensitive)
- **Aluminum is critical** ("really important to our business")
- **Steel prices matter** ("really important")

### Competitive context:
- **Amazon Business** is primary disruptor ($25B in sales)
- B2B ecommerce pricing pressure

### Success metric:
Jenna can easily excerpt content for her weekly newsletter to leadership

---

## CRITICAL: Content Isolation

This codebase was forked from an unrelated client project.
**ZERO contamination from that project may appear in any Grainger output.**

### Automated Protections:
- `config/content_blocklist.py` - Defines blocked terms/patterns
- `tests/test_content_isolation.py` - Validates no contamination
- Document generator validates all output before saving
- Pre-commit hook blocks commits with contamination

### Before EVERY Commit:
```bash
pytest tests/test_content_isolation.py -v
```

### If contamination is detected:
1. Do NOT commit
2. Run `pytest tests/test_content_isolation.py -v` to identify source
3. Remove the contaminated content
4. Re-run validation

---

**Public API** (Stripe-style minimal):
```python
from mro_intelligence import generate_report
report = await generate_report()  # Returns Path to .docx
```

## Dev Environment

```bash
# Install dependencies
pip install -e ".[dev]"

# Environment variables (create .env file)
ERGOMIND_API_KEY=...
ERGOMIND_USER_ID=...
GTA_API_KEY=...
FRED_API_KEY=...
ANTHROPIC_API_KEY=...  # Optional, for AI-enhanced summaries
```

## Testing

**Use context-efficient runner** (shows minimal output on success, full on failure):
```bash
~/.claude/hooks/run-silent python3 -m pytest tests/
~/.claude/hooks/run-silent python3 -m mypy mro_intelligence --ignore-missing-imports
```

**Test structure:**
- `tests/unit/` - Unit tests for individual components
- `tests/integration/` - Integration tests for component interactions
- `tests/e2e/` - End-to-end pipeline tests
- `tests/benchmarks/` - Performance benchmarks

**Coverage target:** 70%+ (currently 72%)

## Code Style

- **Type hints required** - All functions must have type annotations
- **Mypy clean** - Zero mypy errors allowed
- **No unused imports** - Use `pyflakes` to check
- **Minimal public API** - Hide complexity behind simple interfaces
- **No facade-on-facade** - Avoid wrapper classes that just delegate

**Import style:**
```python
# Good - import from actual implementation
from mro_intelligence.core.processors.merger import IntelligenceMerger

# Bad - import through re-export facade
from mro_intelligence.core.processor import IntelligenceMerger
```

## Architecture

```
mro_intelligence/
├── api.py              # Public API (generate_report)
├── cli.py              # Main orchestration class
├── clients/            # External API clients (ErgoMind, GTA, FRED)
├── core/
│   ├── orchestrator.py # Query orchestration
│   ├── processor.py    # Re-exports only (backwards compat)
│   ├── processors/     # Actual processing logic
│   │   ├── base.py     # IntelligenceItem dataclass
│   │   ├── ergomind.py # ErgoMind processor
│   │   ├── gta.py      # GTA processor
│   │   ├── fred.py     # FRED processor
│   │   └── merger.py   # Multi-source merging
│   └── document/       # Word doc generation
├── ai/                 # AI-enhanced content generation
├── config/             # Client sector configuration
├── utils/              # Caching, config, retry logic
└── web/                # FastAPI web interface
```

## Quality Standards

Before any commit, verify:
1. `~/.claude/hooks/run-silent python3 -m pytest tests/` - All tests pass
2. `~/.claude/hooks/run-silent python3 -m mypy mro_intelligence --ignore-missing-imports` - Zero errors
3. `python3 -m pyflakes mro_intelligence` - No unused imports

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
- Verify: `python3 -m pyflakes mro_intelligence/`

**3. Config Organization (P2)**
- [ ] Single config location (inside package: `mro_intelligence/config/`)
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

Run before committing (or use pre-commit hook):
```bash
./scripts/quality-check.sh
```

This script enforces:
- P0: Import hygiene (blocking)
- P1: Dead code warnings
- P2: Config organization (blocking)
- P3: Module exports (blocking)
- P4: File size warnings
- All tests must pass

---

## PR Guidelines

**Commit message format:**
```
<type>: <description>

<body>

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>
```

**Types:** fix, feat, refactor, docs, test, chore

## Anti-Patterns to Avoid

1. **Dead code** - Delete unused classes, methods, parameters
2. **Facade bloat** - Don't create wrapper files that just re-export
3. **Unused imports** - Remove them immediately
4. **Bare except** - Always specify exception types: `except (ValueError, TypeError):`
5. **f-strings without placeholders** - Use regular strings instead
6. **Over-engineering** - Minimal code that solves the problem

## Security

- Never commit `.env` or API keys
- PII sanitization is handled by `ai/pii_sanitizer.py`
- Fact validation via `ai/fact_validator.py`
