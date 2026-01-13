# Development Environment Setup

This guide covers setting up a local development environment for JobSeekers Shovel.

---

## Prerequisites

- **Python 3.11+** (Python 3.11 or higher recommended)
- **Git** (for version control)
- **Text editor or IDE** (VS Code, PyCharm, etc.)
- **(Optional) Node.js** - Only if using a frontend build tool (not required for vanilla JS)

---

## Initial Setup

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/jobseekers-shovel.git
cd jobseekers-shovel
```

### 2. Create Python Virtual Environment

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

### 3. Install Python Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Create Configuration Files

```bash
# Copy example company configuration
cp config/companies.example.yml config/companies.yml

# Edit companies.yml to add your target companies
# (ingestion.yml is already configured with defaults)
```

### 5. Create Required Directories

The directory structure should already exist, but verify:

```bash
# Verify directories exist
ls -la data/jobs
ls -la data/history
ls -la config
```

---

## Configuration

### Company Watchlist (`config/companies.yml`)

Edit `config/companies.yml` to add your target companies:

```yaml
version: 1

companies:
  - id: your-company-id
    name: Your Company Name
    adapter: greenhouse  # or lever, workday
    sources:
      - url: https://boards.greenhouse.io/yourcompany
    metadata:
      tags: [industry, specialization]
      priority: high
      notes: "Focus areas or notes"
```

**Supported adapters:**
- `greenhouse` - Greenhouse ATS
- `lever` - Lever ATS
- `workday` - Workday ATS

### Ingestion Settings (`config/ingestion.yml`)

Default settings are production-ready, but you can adjust:

- `schedule.frequency_hours` - How often to run ingestion (default: 6 hours)
- `crawling.request_delay_seconds` - Delay between requests (default: 2 seconds)
- `classification.repost_window_days` - Repost detection window (default: 30 days)
- `lifecycle.missing_timeout_days` - Days until job marked closed (default: 10 days)

---

## Running Locally

### Manual Ingestion

Run job ingestion manually:

```bash
# Activate virtual environment first
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Run ingestion
python -m src.ingestion.orchestrator
```

### View Frontend Locally

Serve the frontend locally:

```bash
# Simple HTTP server (Python 3)
cd frontend
python -m http.server 8000

# Open browser to http://localhost:8000
```

Alternatively, use any static file server:
```bash
# Using Node.js http-server
npx http-server frontend -p 8000
```

---

## Development Workflow

### 1. Make Code Changes

Edit files in `src/` for backend logic or `frontend/` for UI.

### 2. Test Changes

```bash
# Run unit tests
pytest

# Run with coverage
pytest --cov=src tests/

# Run specific test file
pytest tests/test_normalizer.py
```

### 3. Manual Testing

```bash
# Run ingestion with verbose logging
python -m src.ingestion.orchestrator --log-level DEBUG

# Check output
cat data/jobs/jobs-v1.json | python -m json.tool
```

### 4. Commit Changes

```bash
git add .
git commit -m "Description of changes"
git push
```

---

## Project Structure

```
jobseekers-shovel/
├── config/              # Configuration files
├── data/                # Data storage (JSON files)
├── src/                 # Python source code
│   ├── ingestion/       # Job ingestion logic
│   ├── processing/      # Classification & normalization
│   ├── storage/         # Data persistence
│   └── utils/           # Utilities
├── frontend/            # Static web interface
├── tests/               # Unit tests
└── docs/                # Documentation
```

---

## Troubleshooting

### Import Errors

If you see `ModuleNotFoundError`:

```bash
# Ensure virtual environment is activated
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

### Configuration Errors

If ingestion fails with config errors:

```bash
# Verify YAML syntax
python -c "import yaml; yaml.safe_load(open('config/companies.yml'))"

# Check for required fields
python -m src.utils.validation --check-config
```

### Data Schema Errors

If you see schema validation errors:

```bash
# Validate existing data against schema
python -m src.storage.reader --validate

# Check schema version mismatch
cat data/jobs/jobs-v1.json | grep "version"
```

### Permission Errors

On Windows, if you see permission errors with virtual environment:

```powershell
# Run PowerShell as Administrator
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

---

## Next Steps

- **Configure companies**: Edit `config/companies.yml` with your target companies
- **Run first ingestion**: Execute `python -m src.ingestion.orchestrator`
- **View results**: Open `frontend/index.html` in a browser
- **Set up automation**: Configure GitHub Actions (see deployment docs)

---

## Additional Resources

- [Configuration Guide](configuration.md) - Detailed configuration options
- [User Guide](user-guide.md) - Using the web interface
- [ARCHITECTURE.md](../ARCHITECTURE.md) - Technical architecture details
- [PRD.md](../PRD.md) - Product requirements
