# Architecture Decision Record

This document records technology stack and architectural decisions for the project.

---

## Technology Stack

### Backend / Ingestion Layer

**Language**: Python 3.11+

**Rationale**:
- Excellent HTTP client libraries (requests, httpx)
- Rich ecosystem for data processing (pandas optional, stdlib sufficient)
- Easy JSON manipulation
- Built-in scheduling compatibility (cron, GitHub Actions)
- Zero-cost: runs locally or in CI

**Key Libraries**:
- `requests` - HTTP client for fetching job postings
- `beautifulsoup4` - HTML parsing for semi-structured sources
- `python-dateutil` - Date/time parsing
- `jsonschema` - Schema validation
- `pyyaml` - Configuration file parsing
- `rapidfuzz` - Fast fuzzy string matching for job signature comparison

### Data Storage

**Format**: JSON files with schema versioning

**Structure**:
```
data/
  jobs/
    jobs-v1.json         # Current job records
    jobs-v1-YYYY-MM-DD.json  # Daily snapshots
  applications/
    applications-v1.json  # Application tracking data
  history/
    observations-YYYY-MM.json  # Historical observations (monthly archives)
```

**Rationale**:
- Human-readable and inspectable
- Git-friendly for change tracking
- No database dependency
- Easy to export and migrate
- Meets zero-cost constraint

### Frontend

**Framework**: Static HTML/CSS/JavaScript (Vanilla JS with modern ES6+)

**Alternative consideration**: Could use React/Vue/Svelte if build step is acceptable

**Rationale for Vanilla JS**:
- Zero build step required
- Maximum portability
- Minimal dependencies
- Fast load times
- Easy to fork and modify

**Key Features**:
- Client-side JSON loading via Fetch API
- Local storage for user preferences and application data
- Responsive CSS Grid/Flexbox layout
- No server-side rendering needed

### Deployment & Automation

**CI/CD**: GitHub Actions

**Scheduled Tasks**:
```yaml
# .github/workflows/ingest-jobs.yml
schedule:
  - cron: '0 */6 * * *'  # Every 6 hours (configurable)
```

**Static Hosting**: GitHub Pages

**Rationale**:
- Free tier sufficient for use case
- Built-in authentication (private repos)
- Automated deployment on push
- Version control for all artifacts
- Meets zero-cost constraint

---

## Architecture Patterns

### Ingestion Architecture

```
┌─────────────────────────────────────────────┐
│  GitHub Actions Scheduled Workflow          │
│  (Runs every N hours)                       │
└─────────────────┬───────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────┐
│  Ingestion Orchestrator                     │
│  - Load company config                      │
│  - Initialize adapters                      │
│  - Coordinate execution                     │
└─────────────────┬───────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────┐
│  ATS Adapters (Strategy Pattern)           │
│  - Greenhouse, Lever, Workday, etc.        │
│  - Each implements: fetch_jobs()            │
└─────────────────┬───────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────┐
│  Job Processor                              │
│  - Normalize job signatures                 │
│  - Classify (New/Repost/Existing)           │
│  - Update temporal tracking                 │
│  - Apply lifecycle rules                    │
└─────────────────┬───────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────┐
│  Data Writer                                │
│  - Validate against schema                  │
│  - Write JSON with atomic operations        │
│  - Create daily snapshots                   │
│  - Commit and push to repo                  │
└─────────────────────────────────────────────┘
```

### Classification Logic

```
Input: Raw job posting from ATS
  │
  ▼
┌────────────────────────────┐
│ Normalize Signature        │
│ - Lowercase                │
│ - Whitespace collapse      │
│ - Abbreviation expansion   │
│ - Location parsing         │
└────────┬───────────────────┘
         │
         ▼
┌────────────────────────────┐
│ Check Exact ID Match       │
│ (source_identifier + URL)  │
└────┬───────────────────────┘
     │
     ├─ Match found ──→ EXISTING
     │
     └─ No match
        │
        ▼
┌────────────────────────────┐
│ Check Signature Match      │
│ (company+title+location)   │
│ within 30-day window       │
└────┬───────────────────────┘
     │
     ├─ Match found ──→ LIKELY REPOST
     │
     └─ No match ──→ NEW
```

### Frontend Architecture

```
┌─────────────────────────────────────────────┐
│  index.html                                 │
│  - Static entry point                       │
│  - Loads CSS and JS modules                 │
└─────────────────┬───────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────┐
│  app.js (Main Controller)                   │
│  - Initialize views                         │
│  - Route between Active Jobs / Applications │
│  - Load data from JSON artifacts            │
└─────────────────┬───────────────────────────┘
                  │
        ┌─────────┴─────────┐
        │                   │
        ▼                   ▼
┌───────────────┐   ┌───────────────┐
│ Active Jobs   │   │ Applications  │
│ View          │   │ View          │
│               │   │               │
│ - Render jobs │   │ - Render apps │
│ - Filter/Sort │   │ - Track stage │
│ - Search      │   │ - Follow-ups  │
└───────┬───────┘   └───────┬───────┘
        │                   │
        └─────────┬─────────┘
                  │
                  ▼
┌─────────────────────────────────────────────┐
│  LocalStorage                               │
│  - User application data                    │
│  - UI preferences                           │
│  - Follow-up reminders                      │
└─────────────────────────────────────────────┘
```

---

## Key Design Decisions

### 1. Stateless Backend, Stateful Frontend

**Decision**: All job discovery state lives in Git-tracked JSON files. All application tracking state lives in browser LocalStorage.

**Rationale**:
- Meets "no continuous backend" constraint
- Easy to backup and restore
- No authentication/authorization complexity
- User owns their data completely

**Trade-off**: Application data is device-specific unless manually exported/imported

### 2. Adapter Pattern for ATS Integration

**Decision**: Each ATS platform gets its own adapter implementing a common interface.

**Rationale**:
- Easy to add new ATS platforms
- Isolates platform-specific logic
- Testable in isolation
- Graceful degradation when one adapter fails

### 3. Signature-Based Job Identity

**Decision**: Jobs are primarily identified by normalized (company + title + location) signature, with source ID as secondary.

**Rationale**:
- Handles unstable IDs across ATS platforms
- Enables repost detection
- Works even when URLs change
- Fuzzy matching handles minor typos

### 4. Git as Version Control and Data Store

**Decision**: All job data is committed to Git and versioned.

**Rationale**:
- Complete audit trail of all changes
- Easy rollback if ingestion errors occur
- No separate backup strategy needed
- Diffs show exactly what changed between runs

### 5. Client-Side Application Tracking

**Decision**: Application metadata stored in browser LocalStorage, not server/Git.

**Rationale**:
- Privacy: application data never leaves user's device
- No authentication needed
- Instant updates without server round-trip
- User controls export timing

**Trade-off**: Data portability requires manual export/import

---

## Configuration Structure

### Company Watchlist (`config/companies.yml`)

```yaml
version: 1
companies:
  - id: acme-corp
    name: ACME Corporation
    adapter: greenhouse
    sources:
      - url: https://boards.greenhouse.io/acmecorp
    metadata:
      tags: [aerospace, r&d]
      priority: high
      notes: "Focus on process engineering roles"

  - id: beta-industries
    name: Beta Industries
    adapter: lever
    sources:
      - url: https://jobs.lever.co/betaindustries
    metadata:
      tags: [manufacturing, automation]
      priority: medium
```

### Ingestion Configuration (`config/ingestion.yml`)

```yaml
version: 1
schedule:
  frequency_hours: 6

crawling:
  request_delay_seconds: 2
  user_agent: "JobSeekersShovel/1.0 (Personal Job Tracker)"
  timeout_seconds: 30
  max_retries: 3

classification:
  repost_window_days: 30
  fuzzy_match_threshold: 0.90

lifecycle:
  missing_timeout_days: 10
  retention_days: 90
```

---

## Directory Structure

```
jobseekers-shovel/
├── .github/
│   └── workflows/
│       ├── ingest-jobs.yml       # Scheduled ingestion
│       └── deploy-frontend.yml   # Deploy to GitHub Pages
├── config/
│   ├── companies.yml             # Company watchlist
│   └── ingestion.yml             # Ingestion settings
├── data/
│   ├── jobs/
│   │   ├── jobs-v1.json          # Current jobs
│   │   └── snapshots/
│   │       └── jobs-v1-2026-01-13.json
│   └── history/
│       └── observations-2026-01.json
├── src/
│   ├── ingestion/
│   │   ├── __init__.py
│   │   ├── orchestrator.py       # Main ingestion coordinator
│   │   ├── adapters/
│   │   │   ├── __init__.py
│   │   │   ├── base.py           # Base adapter interface
│   │   │   ├── greenhouse.py
│   │   │   ├── lever.py
│   │   │   └── workday.py
│   │   └── crawler.py            # HTTP client with rate limiting
│   ├── processing/
│   │   ├── __init__.py
│   │   ├── normalizer.py         # Signature normalization
│   │   ├── classifier.py         # Job classification logic
│   │   ├── lifecycle.py          # Lifecycle state management
│   │   └── temporal.py           # Temporal tracking
│   ├── storage/
│   │   ├── __init__.py
│   │   ├── schema.py             # JSON schema definitions
│   │   ├── reader.py             # Data loading
│   │   └── writer.py             # Data persistence
│   └── utils/
│       ├── __init__.py
│       ├── config.py             # Config loading
│       ├── logging.py            # Logging setup
│       └── validation.py         # Input validation
├── frontend/
│   ├── index.html
│   ├── css/
│   │   └── styles.css
│   ├── js/
│   │   ├── app.js                # Main application
│   │   ├── data-loader.js        # JSON data loading
│   │   ├── views/
│   │   │   ├── active-jobs.js
│   │   │   └── applications.js
│   │   └── utils/
│   │       ├── filters.js
│   │       ├── search.js
│   │       └── storage.js        # LocalStorage wrapper
│   └── assets/
├── tests/
│   ├── test_normalizer.py
│   ├── test_classifier.py
│   └── test_adapters.py
├── docs/
│   ├── setup.md
│   ├── configuration.md
│   └── user-guide.md
├── ARCHITECTURE.md               # This file
├── PRD.md
├── AGENTS.md
├── TASKLIST.md
├── CHANGELOG.md
├── README.md
├── requirements.txt              # Python dependencies
└── .gitignore
```

---

## Data Schema

### Job Record Schema (v1)

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "version": "1.0.0",
  "type": "object",
  "properties": {
    "id": {
      "type": "string",
      "description": "Internal unique identifier (UUID)"
    },
    "company_id": {
      "type": "string",
      "description": "References company in config"
    },
    "company_name": {
      "type": "string"
    },
    "title": {
      "type": "string"
    },
    "location": {
      "type": "string"
    },
    "url": {
      "type": "string",
      "format": "uri"
    },
    "source_identifier": {
      "type": ["string", "null"],
      "description": "ATS-specific job ID"
    },
    "signature": {
      "type": "string",
      "description": "Normalized signature for matching"
    },
    "status": {
      "type": "string",
      "enum": ["active", "missing", "closed", "reopened"]
    },
    "classification": {
      "type": "string",
      "enum": ["new", "repost", "existing"]
    },
    "classification_reasoning": {
      "type": "string",
      "description": "Explanation of classification decision"
    },
    "first_seen": {
      "type": "string",
      "format": "date-time"
    },
    "last_seen": {
      "type": "string",
      "format": "date-time"
    },
    "observations": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "timestamp": {"type": "string", "format": "date-time"},
          "source_identifier": {"type": ["string", "null"]},
          "url": {"type": "string"}
        }
      }
    },
    "created_at": {
      "type": "string",
      "format": "date-time"
    },
    "updated_at": {
      "type": "string",
      "format": "date-time"
    }
  },
  "required": [
    "id", "company_id", "company_name", "title",
    "location", "url", "signature", "status",
    "classification", "first_seen", "last_seen"
  ]
}
```

### Application Record Schema (v1)

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "version": "1.0.0",
  "type": "object",
  "properties": {
    "job_id": {
      "type": "string",
      "description": "References job record"
    },
    "applied_date": {
      "type": "string",
      "format": "date"
    },
    "stage": {
      "type": "string",
      "enum": ["applied", "screening", "interview", "rejected", "offer"]
    },
    "notes": {
      "type": "string"
    },
    "contact_person": {
      "type": ["string", "null"]
    },
    "referral_source": {
      "type": ["string", "null"]
    },
    "salary_info": {
      "type": ["string", "null"]
    },
    "follow_ups": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "timestamp": {"type": "string", "format": "date-time"},
          "type": {"type": "string", "enum": ["application", "follow-up"]},
          "notes": {"type": "string"}
        }
      }
    },
    "next_follow_up": {
      "type": ["string", "null"],
      "format": "date"
    }
  },
  "required": ["job_id", "applied_date", "stage"]
}
```

---

## Security Considerations

1. **No Credentials in Repo**: Never commit API keys or credentials. Use environment variables or GitHub Secrets.

2. **Rate Limiting**: Respect target sites with configurable delays and User-Agent identification.

3. **robots.txt Compliance**: Check robots.txt where feasible, though many ATS career pages allow crawling.

4. **Data Privacy**: Application tracking data stays client-side. Job data is public information from career pages.

5. **Input Validation**: Validate all configuration files and ingested data against schemas.

---

## Performance Considerations

1. **Parallel Ingestion**: Fetch jobs from different companies concurrently (with rate limits).

2. **Incremental Processing**: Only reprocess changed jobs, not entire dataset.

3. **Frontend Pagination**: Implement virtual scrolling or pagination for large job lists.

4. **Data Archival**: Move old observations to monthly archives to keep main data file small.

5. **Caching**: Cache normalized signatures and classification results to avoid recomputation.

---

## Testing Strategy

1. **Unit Tests**: Test normalizer, classifier, lifecycle logic in isolation.

2. **Integration Tests**: Test full ingestion pipeline with mock HTTP responses.

3. **Snapshot Tests**: Compare ingestion outputs against known-good snapshots.

4. **Manual Testing**: Real-world testing with 5-10 companies over 2 weeks before scaling to 50+.

5. **Validation Tests**: Verify classification accuracy and false positive rates against test dataset.
