# AGENTS.md

Configuration for AI coding agents working on this project.

## Project Overview

Solairus Intelligence Report Generator - generates monthly geopolitical/economic intelligence reports for aviation clients by aggregating data from ErgoMind, GTA (Global Trade Alert), and FRED (Federal Reserve Economic Data).

**Public API** (Stripe-style minimal):
```python
from solairus_intelligence import generate_report
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
~/.claude/hooks/run-silent python3 -m mypy solairus_intelligence --ignore-missing-imports
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
from solairus_intelligence.core.processors.merger import IntelligenceMerger

# Bad - import through re-export facade
from solairus_intelligence.core.processor import IntelligenceMerger
```

## Architecture

```
solairus_intelligence/
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
2. `~/.claude/hooks/run-silent python3 -m mypy solairus_intelligence --ignore-missing-imports` - Zero errors
3. `python3 -m pyflakes solairus_intelligence` - No unused imports

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
