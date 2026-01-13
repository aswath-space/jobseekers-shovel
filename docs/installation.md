# Installation and Setup

## Prerequisites

- Python 3.11+
- Git
- GitHub account (for deployment)

## Local Setup

### 1. Clone Repository

```bash
git clone <repository-url>
cd jobseekers-shovel
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Companies

Edit `config/companies.yaml`:

```yaml
companies:
  - id: anthropic
    name: Anthropic
    adapter_type: greenhouse
    adapter_config:
      board_token: anthropic
```

**Required fields**:
- `id`: Unique identifier (lowercase, no spaces)
- `name`: Display name
- `adapter_type`: `greenhouse` or `lever`
- `adapter_config.board_token`: Company's job board token

**Finding board tokens**:
- Greenhouse: Check `https://boards.greenhouse.io/[token]`
- Lever: Check `https://jobs.lever.co/[token]`

### 4. Run Initial Ingestion

```bash
python -m src.ingestion
```

Output location: `data/jobs/jobs-v1.json`

### 5. View Jobs

Open `frontend/index.html` in browser, or serve locally:

```bash
python -m http.server 8000 --directory frontend
```

Access at `http://localhost:8000`

## GitHub Pages Deployment

### 1. Enable GitHub Pages

Repository Settings → Pages → Source: GitHub Actions

### 2. Push to Main Branch

Workflows trigger automatically:
- `.github/workflows/ingest-jobs.yml` - Daily at 2 AM UTC
- `.github/workflows/deploy-frontend.yml` - On frontend/data changes

### 3. Access Deployed Site

Site URL: `https://[username].github.io/[repository-name]/`

## Configuration Options

### Ingestion Settings

Edit `config/config.yaml`:

```yaml
ingestion:
  repost_window_days: 30        # Repost detection window
  similarity_threshold: 0.90    # Match threshold (0.0-1.0)
  missing_job_timeout_days: 14  # Days before marking job closed
  rate_limit_delay_seconds: 1.0 # Delay between requests
```

### Data Directory

Change data location in `src/ingestion/orchestrator.py`:

```python
store = JobStore(data_dir="custom/path")
```

## Verification

Run tests to verify installation:

```bash
pytest tests/ -v
```

Expected: 77 tests passing

## Troubleshooting

**Import errors**: Ensure working directory is repository root

**Rate limiting**: Increase `rate_limit_delay_seconds` in config

**No jobs ingested**: Verify board token in `companies.yaml`

**GitHub Actions fails**: Check Actions tab for error logs
