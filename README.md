# Solairus Intelligence Report Generator

## 🎯 Overview

An elegant, professional tool that generates monthly intelligence reports for Solairus Aviation by integrating three complementary intelligence sources:

- **ErgoMind Flashpoints Forum**: Narrative intelligence and geopolitical analysis
- **Global Trade Alert (GTA)**: Concrete trade policy and tariff data
- **Federal Reserve Economic Data (FRED)**: Economic indicators and market metrics

The system produces a two-page executive report:

- **Page 1**: Aviation-specific intelligence relevant to Solairus operations
- **Page 2**: Client-sector intelligence tailored to their diverse client base

## ✨ Features

- **Intelligent Query Orchestration**: Strategic queries designed to extract maximum value from Flashpoints Forum
- **"So What" Analysis**: Every piece of intelligence includes actionable insights
- **Sector Personalization**: Intelligence categorized by client industry (Technology, Finance, Real Estate, Entertainment)
- **Professional Output**: Beautiful DOCX reports optimized for Google Docs
- **Quality Assurance**: Built-in relevance scoring and confidence metrics
- **Simple Interface**: One-click report generation via web UI

## 🏗️ Architecture

```
┌───────────────────────────────────────────────────┐
│          Web Interface (FastAPI)                   │
│        Simple, elegant control panel               │
└───────────────────┬───────────────────────────────┘
                    │
┌───────────────────▼───────────────────────────────┐
│         Multi-Source Intelligence Pipeline         │
│  • Query Orchestrator (Parallel source gathering)  │
│  • ErgoMind Client (Narrative intelligence)        │
│  • GTA Client (Trade policy data)                  │
│  • FRED Client (Economic indicators)               │
│  • Intelligence Processor (Merge & "So What")      │
│  • Document Generator (Professional DOCX)          │
└────────────────────────────────────────────────────┘
```

### Intelligence Sources

1. **ErgoMind Flashpoints Forum** (Primary narrative source)
   - Geopolitical analysis and expert insights
   - Strategic intelligence on global events
   - Aviation-specific threat assessments

2. **Global Trade Alert (GTA)** (Trade data provider)
   - Tariff changes and trade barriers
   - Export controls and sanctions
   - Country-specific trade policies

3. **Federal Reserve Economic Data (FRED)** (Economic metrics)
   - Jet fuel prices (WJFUELUSGULF)
   - Interest rates (Federal Funds, 10-Year Treasury)
   - Inflation indicators (CPI, Core CPI)
   - GDP growth and employment data

## 📋 Requirements

- Python 3.11+
- **ErgoMind API access**: Provides narrative intelligence structure
- **Global Trade Alert (GTA) API key**: Get free key from [Global Trade Alert](https://www.globaltradealert.org/)
- **Federal Reserve Economic Data (FRED) API key**: Get free key from [FRED API](https://fred.stlouisfed.org/docs/api/api_key.html)
- 2GB RAM minimum
- Internet connection for API queries

## 🚀 Quick Start

### Local Development

1. **Clone the repository**
```bash
git clone https://github.com/ofahy3/SolairusDeliverable.git
cd solairus-intelligence
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Set up environment variables**
```bash
# Copy example environment file
cp .env.example .env

# Edit .env and add your API keys:
# - ERGOMIND_API_KEY
# - GTA_API_KEY (get from https://www.globaltradealert.org/)
# - FRED_API_KEY (get from https://fred.stlouisfed.org/docs/api/api_key.html)
```

Note: The system will work without GTA/FRED API keys but will only use ErgoMind data.

4. **Run the web application**
```bash
python3 -m solairus_intelligence.web.app
```

5. **Open your browser**
Navigate to `http://localhost:8080`

6. **Generate a report**
- Click "Generate Intelligence Report"
- Use "Test Mode" for faster generation with limited queries
- Wait for processing (1-5 minutes depending on mode)
- Download the generated DOCX file

### Command Line Usage

For direct command-line generation:

```bash
# Full production report
python3 -m solairus_intelligence.cli

# Test mode (limited queries)
python3 -m solairus_intelligence.cli --test

# Focus on specific areas
python3 -m solairus_intelligence.cli --focus technology finance
```

## ☁️ Google Cloud Deployment

### Prerequisites
- Google Cloud account
- `gcloud` CLI installed and configured
- Cloud Run API enabled

### Deployment Steps

1. **Build the container**
```bash
docker build -t solairus-intelligence .
```

2. **Tag for Google Container Registry**
```bash
docker tag solairus-intelligence gcr.io/[YOUR-PROJECT-ID]/solairus-intelligence
```

3. **Push to GCR**
```bash
docker push gcr.io/[YOUR-PROJECT-ID]/solairus-intelligence
```

4. **Deploy to Cloud Run**
```bash
gcloud run deploy solairus-intelligence \
  --image gcr.io/[YOUR-PROJECT-ID]/solairus-intelligence \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --memory 2Gi \
  --timeout 600
```

### Using Cloud Build (Recommended)

Create `cloudbuild.yaml`:

```yaml
steps:
  # Build the container image
  - name: 'gcr.io/cloud-builders/docker'
    args: ['build', '-t', 'gcr.io/$PROJECT_ID/solairus-intelligence', '.']

  # Push to Container Registry
  - name: 'gcr.io/cloud-builders/docker'
    args: ['push', 'gcr.io/$PROJECT_ID/solairus-intelligence']

  # Deploy to Cloud Run
  - name: 'gcr.io/cloud-builders/gcloud'
    args:
      - 'run'
      - 'deploy'
      - 'solairus-intelligence'
      - '--image'
      - 'gcr.io/$PROJECT_ID/solairus-intelligence'
      - '--region'
      - 'us-central1'
      - '--platform'
      - 'managed'
      - '--allow-unauthenticated'
      - '--memory'
      - '2Gi'
      - '--timeout'
      - '600'
```

Then deploy with:
```bash
gcloud builds submit --config cloudbuild.yaml
```

## 📊 Report Structure

### Page 1: Solairus Business Intelligence
- **Executive Summary**: Top 4 critical findings
- **Geopolitical Developments**: Impact on aviation operations
- **Economic Indicators**: Business aviation demand signals
- **Regional Risk Assessments**: North America, Europe, Asia-Pacific, Middle East
- **Regulatory Horizon**: Upcoming compliance requirements

### Page 2: Client Sector Intelligence
- **Technology Sector**: Silicon Valley dynamics, export controls, data sovereignty
- **Financial Sector**: Market volatility, M&A activity, regulatory changes
- **Real Estate Sector**: Construction costs, development trends, interest rate impacts
- **Entertainment Sector**: Content regulation, production incentives, talent mobility

## 🔧 Configuration

### Modifying ErgoMind Connection

Edit `solairus_intelligence/clients/ergomind_client.py`:
```python
@dataclass
class ErgoMindConfig:
    base_url: str = "https://bl373-ergo-api.toolbox.bluelabellabs.io"
    api_key: str = "7YBp4W2AjAp0"  # Update if needed
    user_id: str = "overwatch@ergo.net"
```

### Adding Client Sectors

Edit `solairus_intelligence/core/processor.py` to add new sectors:
```python
ClientSector.NEW_SECTOR: {
    'companies': ['Company1', 'Company2'],
    'keywords': ['relevant', 'keywords'],
    'geopolitical_triggers': ['specific', 'triggers']
}
```

### Customizing Queries

Edit `solairus_intelligence/core/orchestrator.py` to modify or add query templates:
```python
QueryTemplate(
    category="your_category",
    query="Your strategic query for ErgoMind?",
    follow_ups=["Follow-up question 1", "Follow-up question 2"],
    priority=8,  # 1-10 scale
    sectors=[ClientSector.RELEVANT_SECTOR]
)
```

## 📈 Quality Metrics

The system tracks quality through:
- **Relevance Score**: How applicable to Solairus (0-1)
- **Confidence Score**: Quality of ErgoMind response (0-1)
- **"So What" Coverage**: Percentage with actionable insights
- **Sector Coverage**: Number of client sectors addressed
- **Action Items**: Percentage with concrete next steps

Target: <25% rewrite rate (core success metric)

## 🐛 Troubleshooting

### ErgoMind Connection Issues
- Verify API key is correct
- Check network connectivity
- Review logs for WebSocket errors
- Test mode bypasses most queries

### Report Generation Fails
- Check `outputs/last_run_status.json` for details
- Ensure sufficient memory (2GB+)
- Verify all Python dependencies installed

### Poor Quality Output
- Review query templates for relevance
- Adjust relevance scoring thresholds
- Ensure ErgoMind is returning quality data
- Check confidence scores in logs

## 🔄 Monthly Workflow

1. **First Monday of Month**: Generate report
2. **Review Output**: Check quality metrics
3. **Upload to Google Docs**: Direct DOCX import
4. **Manual Review**: Fact-check and polish
5. **Deliver to Solairus**: Final formatted report

## 📝 Development Notes

- **Test Mode**: Uses only high-priority queries (3 instead of 15+)
- **Rate Limiting**: 2-3 second delays between ErgoMind queries
- **Retry Logic**: Exponential backoff for failed queries
- **Caching**: Responses cached to prevent duplicate queries
- **Error Handling**: Comprehensive logging at each stage

## 🎨 Design Principles

Following "Stop Coding and Start Planning" methodology:
- **Prototype First**: Test ErgoMind integration before building
- **Iterate on Quality**: Multiple processing passes for relevance
- **Simple Over Complex**: Vanilla JavaScript, standard Python
- **Reliability First**: Extensive error handling over features
- **Professional Output**: Focus on document quality over UI polish

## 📧 Support

For issues or questions:
- Check logs in `outputs/`
- Review ErgoMind connection status
- Verify API credentials
- Test with limited queries first

## 🚀 Future Enhancements

- [ ] Client-specific report generation
- [ ] Historical trend analysis
- [ ] Automated scheduling (cron/Cloud Scheduler)
- [ ] Multi-format export (PDF, HTML)
- [ ] Enhanced visualizations
- [ ] Collaborative review features
- [ ] Integration with Google Docs API
- [ ] Advanced caching strategies

## 📜 License

Proprietary - Solairus Aviation Internal Use Only

---

**Built with craftsmanship for Solairus Aviation**
*Powered by ErgoMind Flashpoints Forum*
