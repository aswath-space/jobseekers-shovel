# Usage Guide

## Running Job Ingestion

Fetch jobs from configured companies:

```bash
python -m src.ingestion
```

Options:
- `--config-dir CONFIG_DIR` - Config directory (default: config)
- `--log-level LEVEL` - Log level: DEBUG, INFO, WARNING, ERROR (default: INFO)
- `--log-file FILE` - Optional log file path

## Viewing Jobs

Open the frontend in a web browser:

```bash
# Serve frontend (requires a simple HTTP server)
cd frontend
python -m http.server 8000
```

Then visit: `http://localhost:8000`

## Configuration

### Companies Watchlist

Edit `config/companies.yml`:

```yaml
companies:
  - id: company-slug
    name: Company Name
    adapter: greenhouse  # or lever, workday
    sources:
      - url: https://boards.greenhouse.io/company
```

### Ingestion Settings

Edit `config/ingestion.yml` to configure:
- Schedule frequency
- Crawling delays
- Classification thresholds
- Lifecycle timeouts

## Application Tracking

Applications are stored in browser LocalStorage. To export:
1. Go to Applications view
2. Use browser dev tools: `app.appTracker.exportToJSON()`
3. Copy the output to a file

## Exporting Data

Jobs can be exported to CSV from the frontend using the "Export CSV" button.
