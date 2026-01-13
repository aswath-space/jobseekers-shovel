# Quick Start Guide

## Prerequisites

- Python 3.11+
- pip

## Installation

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure companies to track:**
   ```bash
   cp config/companies.example.yml config/companies.yml
   # Edit config/companies.yml with your target companies
   ```

## Usage

### Step 1: Run Job Ingestion

Fetch jobs from configured companies:

```bash
python -m src.ingestion
```

This will:
- Fetch jobs from all companies in `config/companies.yml`
- Classify them as NEW, REPOST, or EXISTING
- Track temporal data (first_seen, last_seen)
- Save to `data/jobs/jobs-v1.json`

### Step 2: View Jobs in Frontend

Open the frontend in your browser:

```bash
cd frontend
python -m http.server 8000
```

Then visit: http://localhost:8000

### Step 3: Track Applications

1. Browse jobs in the "Active Jobs" view
2. Click "Track Application" on any job
3. Fill in application details (date, stage, notes, follow-up date)
4. View all applications in the "Applications" view

## Example Configuration

`config/companies.yml`:

```yaml
companies:
  - id: anthropic
    name: Anthropic
    adapter: greenhouse
    sources:
      - url: https://boards.greenhouse.io/anthropic

  - id: openai
    name: OpenAI
    adapter: lever
    sources:
      - url: https://jobs.lever.co/openai
```

## Key Features

- **Automatic Classification**: Detects NEW jobs, REPOSTS (with 90% fuzzy matching), and tracks EXISTING jobs
- **Temporal Tracking**: See when jobs were first/last seen
- **Lifecycle Management**: Jobs marked MISSING if not seen, CLOSED after timeout
- **Application Tracking**: Track where you've applied with stage management
- **Follow-up Alerts**: Visual indicators for jobs needing follow-up
- **Search & Filter**: Find jobs by title, company, location, status
- **Export**: Export jobs to CSV for analysis

## Running Tests

```bash
pytest tests/ -v
```

All 61 tests should pass.

## Troubleshooting

**Jobs not loading?**
- Ensure you've run `python -m src.ingestion` first
- Check `data/jobs/jobs-v1.json` exists

**Frontend blank?**
- Serve via HTTP server (not file://)
- Check browser console for errors
- Ensure data file path is correct

**Rate limiting errors?**
- Adjust `crawling.request_delay` in `config/ingestion.yml`
- Default is 2 seconds between requests

## Next Steps

See [docs/usage.md](docs/usage.md) for detailed usage instructions.
