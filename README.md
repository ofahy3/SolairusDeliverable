# Grainger MRO Intelligence Report Generator

## Overview

Generates biweekly MRO (Maintenance, Repair & Operations) market intelligence reports for W.W. Grainger by integrating three intelligence sources:

- **ErgoMind Flashpoints Forum**: Geopolitical analysis and narrative intelligence
- **Global Trade Alert (GTA)**: Trade policy, tariffs, and supply chain data
- **FRED (Federal Reserve Economic Data)**: Economic indicators for industrial activity

The system produces a **3-page executive report** translating global events into MRO market implications for Grainger's key sectors: Manufacturing, Construction, Energy, Transportation/Logistics, and Agriculture.

---

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure API Keys

Create a `.env` file in the project root:

```bash
# Required - ErgoMind access
ERGOMIND_API_KEY=your_ergomind_key
ERGOMIND_USER_ID=your_user_id

# Required - Economic data
FRED_API_KEY=your_fred_key          # Get free: https://fred.stlouisfed.org/docs/api/api_key.html

# Optional - Trade policy data
GTA_API_KEY=your_gta_key            # Get from: https://www.globaltradealert.org/

# Optional - AI-enhanced summaries
ANTHROPIC_API_KEY=your_anthropic_key
```

### 3. Generate a Report

**Test mode** (faster, limited queries - use for testing):
```bash
python3 -m mro_intelligence.cli --test
```

**Full report** (production quality):
```bash
python3 -m mro_intelligence.cli
```

### 4. Find Your Report

Reports are saved to:
```
outputs/MRO_Intelligence_Report_[Month]_[Timestamp].docx
```

Example: `outputs/MRO_Intelligence_Report_December_2024_20241211_143022.docx`

---

## Report Structure (3 Pages)

### Page 1: Executive Summary & Macro Outlook
- **Introduction**: Context on Ergo Flashpoints Forum data (last 3 months)
- **Executive Summary**: Top 4-5 key findings with MRO market implications
- **US Economic Outlook**: GDP, industrial production, manufacturing trends
- **Key Economic Indicators Table**: FRED data with MRO relevance column

### Page 2: Sector Demand Analysis
- **Manufacturing Sector**: Production trends, capex investment, automation
- **Construction Sector**: Building activity, infrastructure spending, permits
- **Energy Sector**: Oil/gas activity, utility maintenance, renewables
- **"So What for Grainger" Callouts**: Blue boxes explaining business implications

### Page 3: Risks & Opportunities
- **Trade Policy Impacts**: Tariffs, supply chain shifts, reshoring trends
- **Regional Considerations**: US domestic and USMCA region focus
- **90-Day Outlook**: Near-term actionable intelligence
- **Recommended Actions**: Concrete next steps for MRO positioning

---

## Biweekly Workflow

### Every 2 Weeks (Per Grainger Cadence)

**Step 1: Generate Report**
```bash
python3 -m mro_intelligence.cli
```
Wait 3-5 minutes for completion.

**Step 2: Review Quality Metrics**
Check the console output for:
- Total intelligence items processed
- Relevance scores (target: >0.6 average)
- Sector coverage (should include Manufacturing, Construction, Energy)

**Step 3: Upload to Google Docs**
- Open the `.docx` file in Google Docs
- Formatting should preserve automatically
- Review for any formatting issues

**Step 4: Internal Review**
- Send to Haden/Client Solutions for review
- Address any feedback or clarifications
- Verify all "So What" statements are actionable

**Step 5: Deliver to Grainger**
- Send final report to Jenna at Grainger
- Note any particularly significant findings in the email

---

## Command Line Options

```bash
# Full production report
python3 -m mro_intelligence.cli

# Test mode (faster, fewer queries)
python3 -m mro_intelligence.cli --test

# Focus on specific sectors
python3 -m mro_intelligence.cli --focus manufacturing construction

# Specify output directory
python3 -m mro_intelligence.cli --output /path/to/output
```

---

## FRED Indicators Tracked

| Category | Indicators |
|----------|------------|
| Industrial Activity | INDPRO, IPMAN, CMRMTSPL, DGORDER |
| Construction | TLRESCONS, TLNRESCONS, HOUST, PERMIT |
| Business Conditions | UNRATE, PCEPILFE, FEDFUNDS, T10Y2Y |
| Commodities | PPIACO, WPU101, DCOILWTICO |

---

## Troubleshooting

### "Failed to connect to ErgoMind"
- Verify `ERGOMIND_API_KEY` and `ERGOMIND_USER_ID` in `.env`
- Check network connectivity
- Try test mode first: `python3 -m mro_intelligence.cli --test`

### Report generation hangs
- ErgoMind queries take 2-5 minutes total
- Check logs in console for progress
- If stuck >10 minutes, cancel and retry

### Empty or low-quality output
- Verify all API keys are set correctly
- Check `outputs/last_run_status.json` for errors
- Ensure FRED_API_KEY is valid (most reliable data source)

### DOCX formatting issues in Google Docs
- The report is optimized for Google Docs import
- If tables break, try reducing browser zoom
- Headers and "So What" boxes should render correctly

### "CONTAMINATION DETECTED" error
- The system blocks any content from prior client projects
- This is a safety feature - do not bypass
- Check source data for unexpected content

---

## Configuration Files

| File | Purpose |
|------|---------|
| `config/grainger_profile.py` | Grainger-specific settings (lookback, relevance filters) |
| `config/content_blocklist.py` | Blocked terms/patterns for content isolation |
| `mro_intelligence/config/clients.py` | MRO sector definitions and keywords |
| `mro_intelligence/clients/fred_client.py` | FRED indicator configuration |

---

## Quality Targets

- **Relevance Score**: >0.6 average (items below 0.6 filtered out)
- **Sector Coverage**: All 5 MRO sectors represented
- **"So What" Coverage**: 100% of items have actionable insights
- **Rewrite Rate**: <25% (reports should need minimal editing)

---

## Support

For issues:
1. Check logs in console output
2. Review `outputs/last_run_status.json`
3. Verify API credentials in `.env`
4. Run tests: `python3 -m pytest tests/test_mro_queries.py -v`

---

**Built for Grainger** | Powered by ErgoMind Flashpoints Forum
