# MRO Intelligence Documentation

This directory contains comprehensive documentation for the MRO Intelligence Report Generator.

## Documentation Structure

- [architecture.md](architecture.md) - System architecture and design decisions
- [deployment.md](deployment.md) - Deployment guide for various environments

## Quick Links

- [Main README](../README.md) - Project overview and quick start
- [CHANGELOG](../CHANGELOG.md) - Version history

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
black mro_intelligence tests
flake8 mro_intelligence tests
mypy mro_intelligence
```

### Running the Application

```bash
# CLI mode (test)
python -m mro_intelligence.cli --test

# Web interface
uvicorn mro_intelligence.web.app:app --reload
```

## Architecture Overview

The system is organized into several key modules:

- **clients/** - External API clients (ErgoMind, GTA, FRED)
- **ai/** - AI content generation and validation
- **core/** - Core business logic (processor, orchestrator, document generator)
- **utils/** - Utilities and configuration
- **web/** - Web interface

## Support

For questions or issues, contact the Grainger development team.
