# Solairus Intelligence Documentation

This directory contains comprehensive documentation for the Solairus Intelligence Report Generator.

## Documentation Structure

- [architecture.md](architecture.md) - System architecture and design decisions
- [deployment.md](deployment.md) - Deployment guide for various environments
- [archive/](archive/) - Historical documentation and project planning

## Quick Links

- [Main README](../README.md) - Project overview and quick start
- [CHANGELOG](../CHANGELOG.md) - Version history
- [LICENSE](../LICENSE) - License information

## For Developers

### Setting Up Development Environment

```bash
# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Install pre-commit hooks
pre-commit install

# Run tests
pytest

# Run linting
black solairus_intelligence tests
flake8 solairus_intelligence tests
mypy solairus_intelligence
```

### Running the Application

```bash
# CLI mode (test)
python -m solairus_intelligence.cli --test

# Web interface
uvicorn solairus_intelligence.web.app:app --reload
```

## Architecture Overview

The system is organized into several key modules:

- **clients/** - External API clients (ErgoMind, GTA, FRED)
- **ai/** - AI content generation and validation
- **core/** - Core business logic (processor, orchestrator, document generator)
- **utils/** - Utilities and configuration
- **web/** - Web interface

## Support

For questions or issues, contact the Solairus Aviation development team.
