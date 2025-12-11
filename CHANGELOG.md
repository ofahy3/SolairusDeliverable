# Changelog

All notable changes to the MRO Intelligence Report Generator will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2025-11-11

### Added
- Initial production release
- **ErgoMind Flashpoints Forum integration** - Primary narrative intelligence source
- **Global Trade Alert (GTA) API integration** - Trade policy and tariff data
- **Federal Reserve Economic Data (FRED) API integration** - Economic indicators
- **AI-powered content generation** with Claude Opus 4
  - AI-enhanced Executive Summary generation
  - AI-generated "So What" statements
  - PII sanitization before external API calls
  - Fact validation to prevent hallucinations
  - Graceful degradation to template system on AI failure
- **Intelligent query orchestration** - Parallel multi-source data gathering
- **"So What" analysis** for all intelligence items
- **Sector-specific intelligence** categorization (Technology, Finance, Real Estate, Entertainment, Energy)
- **Professional DOCX report generation** optimized for Google Docs
- **Web interface** with FastAPI for one-click report generation
- **CLI interface** for command-line report generation
- **Docker containerization** with Cloud Run support
- **Environment-aware configuration** (local/Docker/cloud auto-detection)
- **Test mode** for faster generation during development
- **Comprehensive logging** and error handling
- **Quality metrics** including relevance scoring and confidence metrics
- **Status tracking** with JSON output

### Features
- Two-page executive report format
  - Page 1: Industrial-specific intelligence
  - Page 2: Client sector intelligence
- Support for multiple client sectors
- ErgoMind narrative leadership with GTA/FRED supporting data
- Freshness filtering (30-day window for relevant intelligence)
- Source attribution for all intelligence items
- Action items generation for each sector
- Regional risk assessments
- Regulatory outlook section

### Technical
- Python 3.11+ support
- Async/await throughout for performance
- WebSocket integration for ErgoMind real-time data
- REST API integration for GTA and FRED
- Composite scoring system (relevance × confidence × freshness × source weight)
- Multi-source deduplication
- Smart content truncation at sentence boundaries

### Infrastructure
- Docker deployment with health checks
- Google Cloud Run configuration
- Environment variable management
- Automatic output directory creation
- Status file tracking

### Security
- PII sanitization before external API calls
- API key management via environment variables
- Proprietary license protection
- Input validation throughout

## [Unreleased]

### Planned
- Automated scheduling with Cloud Scheduler
- Historical trend analysis and comparison
- Multi-format export (PDF, HTML, Markdown)
- Google Docs API direct integration
- Enhanced data visualizations and charts
- Client-specific report customization
- Email delivery integration
- Archive and search functionality for past reports
- Performance metrics dashboard
- API rate limiting and caching
- Multi-language support
- Advanced AI features:
  - Trend detection
  - Anomaly identification
  - Predictive analytics
  - Sentiment analysis

---

[1.0.0]: https://github.com/mro/intelligence-report-generator/releases/tag/v1.0.0
