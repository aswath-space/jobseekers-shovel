# Architecture and Design Decisions

## System Overview

JobSeekers Shovel is a deterministic job tracking system with three main components:

1. **Ingestion Pipeline**: Fetches jobs from company boards
2. **Classification Engine**: Detects reposts and tracks temporal state
3. **Frontend Interface**: Displays jobs and manages application tracking

## Design Principles

**Deterministic over Statistical**: All classification is rule-based with explainable reasoning. No ML models, no randomness.

**Local-First**: Single-user tool with local data storage. No server required.

**Zero-Cost Operation**: Runs on GitHub free tier. No paid services.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────┐
│                 Ingestion Pipeline                  │
├─────────────────────────────────────────────────────┤
│  Adapters (Greenhouse, Lever)                       │
│       ↓                                              │
│  Normalizer (title, location)                       │
│       ↓                                              │
│  Classifier (new/existing/repost/reopened)          │
│       ↓                                              │
│  Matcher (component-wise similarity)                │
│       ↓                                              │
│  JobStore (JSON persistence)                        │
│       ↓                                              │
│  VersionManager (snapshots)                         │
└─────────────────────────────────────────────────────┘
           ↓ writes jobs-v1.json ↓
┌─────────────────────────────────────────────────────┐
│                 Frontend (Static)                    │
├─────────────────────────────────────────────────────┤
│  DataLoader (loads jobs-v1.json)                    │
│  AppTracker (localStorage for applications)         │
│  App (rendering, filtering, export)                 │
└─────────────────────────────────────────────────────┘
```

## Component Details

### Ingestion Pipeline

**Purpose**: Fetch jobs from company career pages, classify, persist

**Flow**:
1. `Orchestrator` coordinates ingestion
2. `Adapter` fetches jobs from Greenhouse/Lever APIs
3. `Normalizer` standardizes titles and locations
4. `Classifier` determines classification based on history
5. `Matcher` finds similar jobs using fuzzy matching
6. `JobStore` saves to JSON with atomic operations
7. `VersionManager` creates timestamped snapshots

**Key Files**:
- `src/ingestion/orchestrator.py`: Main coordinator
- `src/ingestion/adapters/`: Platform-specific fetchers
- `src/processing/normalizer.py`: Text normalization
- `src/processing/classifier.py`: Classification logic
- `src/processing/matcher.py`: Similarity matching
- `src/storage/job_store.py`: JSON persistence

### Classification Engine

**Purpose**: Categorize jobs as new/existing/repost/reopened

**Algorithm**:
1. Generate signature: `company|normalized_title|normalized_location`
2. Search known jobs for matches within repost window (30 days)
3. Use component-wise similarity: company (10%), title (60%), location (30%)
4. Threshold: 90% similarity = match
5. Return classification with reasoning

**Matcher Design Decision**:
- **Original**: Full string comparison → failed on word order
- **Implemented**: Component-wise with `token_sort_ratio` for titles
- **Result**: 100% repost detection (exceeds 90% target)

**Signature Example**:
```
Input: "Senior Software Engineer" at "San Francisco, CA" for "Anthropic"
Normalized: "anthropic|senior software engineer|san francisco california"
```

### Temporal Tracking

**Purpose**: Track job lifecycle (first seen, last seen, status transitions)

**State Machine**:
```
NEW → ACTIVE ⟷ MISSING → CLOSED
              ↓
           REOPENED
```

**Transitions**:
- NEW: First observation
- ACTIVE: Reobserved within repost window
- MISSING: Not seen for >30 days
- CLOSED: Missing for >14 days
- REOPENED: Reappears after closure

### Data Persistence

**Format**: Single JSON file (`data/jobs/jobs-v1.json`)

**Schema**:
```json
{
  "version": "1.0.0",
  "generated_at": "ISO-8601",
  "job_count": 123,
  "jobs": [
    {
      "id": "uuid",
      "company_id": "anthropic",
      "company_name": "Anthropic",
      "title": "Software Engineer",
      "location": "San Francisco, CA",
      "status": "active",
      "classification": "new",
      "classification_reasoning": "...",
      "signature": "anthropic|software engineer|san francisco california",
      "first_seen": "ISO-8601",
      "last_seen": "ISO-8601",
      "observations": [...]
    }
  ]
}
```

**Atomic Operations**: Writes use temp file + rename pattern for crash safety

**Versioning**: Automatic snapshots after each save, 30-day retention

### Frontend Architecture

**Technology**: Vanilla JavaScript (no framework)

**Rationale**: Zero build step, works offline, simple deployment

**Components**:
- `DataLoader`: Fetches and filters jobs
- `AppTracker`: Manages application state in localStorage
- `App`: Main controller for views and interactions

**State Management**: No global state. DOM as source of truth.

**Data Flow**:
```
jobs-v1.json → DataLoader → App → Render → DOM
localStorage → AppTracker → App → Render → DOM
```

## Key Design Decisions

### 1. Deterministic Classification

**Decision**: Use rule-based fuzzy matching instead of ML

**Rationale**:
- Explainable: Users see exact reasoning
- Consistent: Same input always produces same output
- No training data needed
- Meets PRD 90% target (achieved 100%)

### 2. Component-Wise Similarity

**Decision**: Split signature matching by field (company, title, location)

**Rationale**:
- Handles word reordering in titles
- Distinguishes seniority levels
- Allows field-specific strategies (exact vs fuzzy)
- Weighted by importance (title > location > company)

**Implementation**: `matcher.py:calculate_similarity()`

### 3. Single JSON File

**Decision**: Store all jobs in one file vs database

**Rationale**:
- Simple deployment (just copy file)
- Easy backup/restore
- Frontend can load directly (no API needed)
- Scales to ~10K jobs before performance issues
- Atomic writes prevent corruption

**Trade-off**: Not suitable for multi-user or >10K jobs

### 4. Static Frontend

**Decision**: No backend server, just HTML/CSS/JS

**Rationale**:
- GitHub Pages hosting (free)
- No server maintenance
- Fast load times
- Works offline
- Easy to customize

**Trade-off**: Limited to read-only operations in browser

### 5. GitHub Actions for Automation

**Decision**: Use GHA for scheduled ingestion vs external cron

**Rationale**:
- Free tier: 2000 minutes/month (enough for daily runs)
- Integrated with repository
- Automatic deployment
- No separate server to maintain

**Trade-off**: Public repos only (or uses paid minutes)

### 6. 30-Day Repost Window

**Decision**: Jobs within 30 days are candidates for repost matching

**Rationale**:
- Most companies repost within this timeframe
- Balances precision (short window) vs recall (long window)
- Configurable in `config.yaml`

### 7. 90% Similarity Threshold

**Decision**: Require 90% match for repost classification

**Rationale**:
- High precision (few false positives)
- Tolerates minor variations (abbreviations, punctuation)
- Distinguishes meaningful differences (seniority)
- Validated to achieve 100% accuracy in controlled tests

### 8. localStorage for Applications

**Decision**: Store application tracking in browser localStorage

**Rationale**:
- No backend needed
- Persists across sessions
- User-specific (no privacy concerns)
- Easy export to JSON

**Trade-off**: Not synced across devices

## Performance Characteristics

**Ingestion**:
- Rate: ~100 jobs/minute (limited by API rate limiting)
- Memory: <100 MB for 10K jobs
- Storage: ~1 MB per 1000 jobs (JSON)

**Classification**:
- Time: O(n) where n = known jobs (linear scan)
- Optimized: Only checks same company, within time window
- Typical: <1ms per job for 1000 known jobs

**Frontend**:
- Load time: <1s for 5000 jobs
- Search/filter: <100ms (client-side JavaScript)
- No pagination needed until ~10K jobs

## Testing Strategy

**Unit Tests**: 77 tests covering:
- Normalizer (11 tests)
- Matcher (16 tests)
- Classifier (15 tests)
- Storage (6 tests)
- Versioning (9 tests)
- Config (4 tests)
- Crawler (9 tests)
- Validation (7 tests)

**Validation Tests**: Controlled scenarios with known ground truth
- 12 scenarios (6 reposts, 6 new)
- 100% repost detection rate
- Deterministic (same result every run)

**Integration Tests**: End-to-end with 307 real Anthropic jobs

## Security Considerations

**No Authentication**: Single-user tool, no auth needed

**Data Privacy**: All data stored locally, no external transmission

**API Keys**: Not required (public job boards)

**XSS Protection**: Minimal risk (static content, no user input)

## Scalability Limits

**Current Design Supports**:
- ~50 companies
- ~10,000 jobs
- Single user
- Daily ingestion

**Would Need Refactor For**:
- >50 companies (API rate limiting issues)
- >10K jobs (frontend performance)
- Multi-user (need authentication, database)
- Real-time updates (need backend push)

## Future Enhancements

**Potential Improvements** (not in current scope):
1. Database backend (PostgreSQL) for >10K jobs
2. Multi-user support with authentication
3. Real-time notifications (email/webhook)
4. Advanced search (regex, boolean queries)
5. Analytics dashboard (trend tracking)
6. Mobile app
7. Browser extension

## Dependencies

**Python**:
- `requests`: HTTP client for API calls
- `rapidfuzz`: Fuzzy string matching
- `pyyaml`: Config file parsing
- `pytest`: Testing framework

**JavaScript**: None (vanilla JS)

**Infrastructure**: GitHub (repository, Actions, Pages)

## File Structure

```
jobseekers-shovel/
├── src/
│   ├── ingestion/          # Ingestion pipeline
│   │   ├── adapters/       # Platform adapters
│   │   └── orchestrator.py
│   ├── processing/         # Classification engine
│   │   ├── classifier.py
│   │   ├── matcher.py
│   │   └── normalizer.py
│   └── storage/            # Data persistence
│       ├── job_store.py
│       └── versioning.py
├── frontend/               # Static web interface
│   ├── index.html
│   ├── css/
│   └── js/
├── tests/                  # Test suite
├── config/                 # Configuration
│   ├── companies.yaml
│   └── config.yaml
├── data/                   # Generated data
│   ├── jobs/
│   └── versions/
└── docs/                   # Documentation
```
