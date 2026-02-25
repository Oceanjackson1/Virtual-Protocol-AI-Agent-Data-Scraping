# Virtual Protocol AI Agent Data Scraping

Automated scraper for [Virtuals Protocol ACP (Agent Commerce Protocol)](https://app.virtuals.io/acp/scan) platform. Collects comprehensive data on all AI agents including metrics, offerings, wallet addresses, and more — exported to a formatted Excel file.

## Features

- **Pure API scraping** — no browser automation needed; reverse-engineered API endpoints for maximum speed and reliability
- **Comprehensive data** — 35 fields per agent across 5 categories (Core Info, Key Metrics, Activity, What I Offer, Identity & Links)
- **Formatted Excel output** — two-level merged headers, hyperlinked Agent IDs, auto-width columns, frozen panes, Chinese-localized content
- **Async & concurrent** — configurable concurrency with rate limiting and retry logic
- **Scheduled runs** — built-in scheduler for daily/hourly automated scraping

## Data Collected

| Category | Fields |
|---|---|
| **Core Info** | Rank, Agent Link (hyperlink), Name, Category, Description |
| **Key Metrics** | Volume (Total AGDP), Gross AGDP, Total Revenue, Success Rate, Rating |
| **Activity** | Transaction Count, Successful Jobs, Unique Buyers, Online Status, Last Active |
| **What I Offer** | Offering Names, Descriptions, Prices, SLA, Requirements |
| **Identity & Links** | Wallet Address, Contract Address, Token Address, Owner Address, Twitter, Symbol, Role, Cluster, Graduated, Balance, Chains, Virtual Agent ID, Created At, Profile Pic URL |

## API Endpoints Used

All data is sourced from `acpx.virtuals.io` public APIs (discovered via Playwright network interception):

| Endpoint | Description |
|---|---|
| `GET /api/agents` | Agent list with offerings and base info |
| `GET /api/metrics/agents` | Leaderboard with volume, revenue, success rate |
| `GET /api/metrics/four-metrics` | Platform-level AGDP time series |
| `GET /api/agents/{id}/details` | Individual agent detail (description, jobs, wallet) |
| `GET /api/metrics/agent/{id}` | Individual agent metrics (volume, revenue, 7d data) |

## Quick Start

### Prerequisites

- Python 3.8+
- pip

### Installation

```bash
git clone https://github.com/Oceanjackson1/Virtual-Protocol-AI-Agent-Data-Scraping.git
cd Virtual-Protocol-AI-Agent-Data-Scraping
pip install -r requirements.txt
```

### Run Once

```bash
python -m src.main
```

Or use the shell script:

```bash
chmod +x run_scraper.sh
./run_scraper.sh
```

Output Excel file will be saved to `./output/acp_agents_YYYYMMDD_HHMMSS.xlsx`.

### Scheduled Mode

1. Edit `config.yaml`:

```yaml
schedule:
  enabled: true
  interval_hours: 24
  run_at: "08:00"
```

2. Start the scheduler:

```bash
./run_scraper.sh schedule
```

Alternatively, use cron:

```bash
# Run daily at 8:00 AM
0 8 * * * cd /path/to/Virtual-Protocol-AI-Agent-Data-Scraping && python -m src.main
```

## Configuration

All settings are in `config.yaml`:

```yaml
scraper:
  concurrency: 3          # parallel API requests
  request_delay_sec: 1.5  # delay between requests
  max_retries: 3          # retry count on failure

output:
  directory: "./output"        # output folder
  filename_prefix: "acp_agents" # Excel file prefix

schedule:
  enabled: false
  interval_hours: 24
  run_at: "08:00"
```

## Project Structure

```
├── config.yaml              # Scraper configuration
├── requirements.txt         # Python dependencies
├── run_scraper.sh           # Launch script
├── src/
│   ├── __init__.py
│   ├── main.py              # Entry point
│   ├── scraper.py           # Core scraper (async API calls)
│   ├── models.py            # Data models (AgentData, Offering, GlobalMetrics)
│   ├── excel_exporter.py    # Excel export (two-level headers, hyperlinks)
│   ├── scheduler.py         # Scheduled execution
│   └── api_discovery.py     # API endpoint discovery tool (Playwright)
└── output/                  # Generated Excel files
```

## Excel Output Format

The generated Excel file uses a single-sheet layout with:

- **Row 1**: Level-1 category headers (merged cells, blue background)
- **Row 2**: Level-2 field headers (light blue background)
- **Row 3+**: Agent data, one row per agent, sorted by Volume (descending)
- **Agent Link column**: clickable hyperlinks to each agent's detail page
- **Frozen panes**: first two header rows stay visible while scrolling
- **Auto-filter**: enabled on all columns
- **Summary section**: scrape timestamp, total agent count, and platform AGDP at the bottom

## Tech Stack

- **aiohttp** — async HTTP client for API calls
- **openpyxl** — Excel file generation with styling
- **PyYAML** — configuration file parsing
- **schedule** — job scheduling
- **Playwright** — API endpoint discovery (optional, only needed for `api_discovery.py`)

## License

MIT
