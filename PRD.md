# Product Requirements Document (PRD)

This document defines the intent, scope, and constraints of the project.

AI agents must evaluate all proposed actions against this document
before execution. If an action contradicts or extends this document,
it must be flagged and not executed silently.

PRD.md may only be modified with explicit intent-level instructions.

---

## Problem Statement

For specialized roles in R&D, process engineering, and manufacturing-adjacent domains, traditional job search workflows based on keyword queries across aggregators are inefficient and cognitively expensive. Roles are inconsistently titled, short-lived, or quietly reposted, and most platforms are stateless: they do not answer the user's real question — *what changed since I last checked?*

Users are forced to manually revisit the same postings repeatedly, imposing significant cognitive load and wasting time re-evaluating roles already dismissed. Existing tools lack historical context, making it impossible to distinguish genuinely new opportunities from minor reposts or unchanged listings.

Additionally, target employers use heterogeneous Applicant Tracking Systems (ATS). Some provide clean, structured endpoints; others regenerate job IDs, temporarily remove postings, or aggressively obscure structure. This makes naive "new job" detection unreliable and prone to false positives.

The core problem is therefore **not job search**, but **reliable detection and interpretation of hiring activity changes over time for a known set of companies**, with minimal noise and manual effort.

---

## Goals

* Detect and surface **meaningful changes** in hiring activity from a curated list of companies.
* Treat **time and change** (first seen, last seen, disappearance, reappearance) as first‑class signals.
* Present a clear distinction between:

  * genuinely new roles
  * likely reposts
  * closed roles
* Provide a lightweight, graphical interface to review jobs and manually track applications.
* Maintain full **data ownership and portability** — all data must be exportable and human-readable.
* Ensure detection logic is **auditable and explainable** — users must understand why a job was classified a certain way.
* Operate as a zero‑cost, forkable, personal tool without requiring a continuously running backend.

---

## Non-Goals

*This section is binding.*

* This project is **not** a general-purpose job board or search engine.
* This project is **not** intended to provide exhaustive coverage of all employers or ATS platforms.
* This project will **not** rely on Selenium, Puppeteer, or full browser automation in the MVP.
* This project will **not** perform automated job applications, outreach, or candidate evaluation.
* This project will **not** include learning systems or outcome-based optimization in the MVP.
* This project will **not** require user accounts, authentication, or centralized data collection.

---

## Functional Requirements

### Company Watchlist

* The system must allow configuration of a fixed list of target companies.
* The system must support at least **50 companies** in the watchlist.
* Company configuration must explicitly separate:

  * Company name
  * Source type (ATS / semi-structured page)
  * One or more source URLs
  * Optional metadata (tags, priority level, notes)
* Each company must be associated with exactly one ingestion strategy.
* Source URLs must be validated for correct format and accessibility.
* The system should gracefully handle company metadata changes (name updates, URL changes).

### Job Ingestion (Scheduled)

* Job ingestion must run periodically as a scheduled task with **configurable frequency** (e.g., hourly, daily, weekly).
* Ingestion must fetch the *current observable set* of job postings per company.
* The system must implement **respectful crawling practices**:

  * Configurable delays between requests (default: minimum 1 second)
  * Appropriate User-Agent headers
  * Respect for robots.txt directives where feasible
* The system must tolerate:

  * unstable or regenerated job IDs
  * temporary disappearance of postings
* Ingestion must include **error handling and logging**:

  * Retry logic for transient failures (configurable attempts and backoff)
  * Detailed error logs for debugging failed ingestions
  * Graceful degradation when individual companies fail
* Ingestion must produce structured records containing at minimum:

  * company
  * job title
  * location
  * job URL
  * source identifier (if available)
  * ingestion timestamp

### Temporal Tracking

* For each job record, the system must track:

  * `first_seen` timestamp (when first observed)
  * `last_seen` timestamp (most recent observation)
  * Individual observation timestamps for historical analysis
* `last_seen` must be updated on every ingestion cycle in which the job is observed.
* The system must maintain a **configurable retention policy** for historical observation data (e.g., retain detailed observations for 90 days, then archive).

### New vs. Repost Classification (Core Logic)

The system must classify job observations into one of the following states:

1. **New**

   * A job whose signature has not been observed before.

2. **Likely Repost**

   * A job observed with a new source identifier or URL,
   * whose normalized signature (company + title + location) matches a job
     seen within a configurable recent window (e.g. 30 days).
   * Likely reposts must not be promoted as strictly new by default.

3. **Existing**

   * A job whose identifier and signature have been continuously observed.

**Signature Normalization Rules:**

The system must define explicit normalization rules for matching:

* **Case folding**: Convert all text to lowercase for comparison
* **Whitespace normalization**: Collapse multiple spaces, trim leading/trailing
* **Title abbreviations**: Handle common variations (e.g., "Sr." ↔ "Senior", "Engr" ↔ "Engineer")
* **Location parsing**: Normalize city/state formats, handle "Remote" variations
* **Punctuation**: Strip or standardize punctuation in titles

The system must support a **configurable similarity threshold** for fuzzy matching (e.g., 90% similarity for titles with minor typos).

Classification must be deterministic and explainable. Each classification decision must include the reasoning (e.g., "Matched existing job ID-123 by normalized signature").

### Job Lifecycle Handling

* If a previously observed job is not seen in a given ingestion run:

  * it must remain active but flagged as "missing" until a configurable timeout.
* If a job is not seen for longer than the timeout window:

  * it must be marked as **closed**.
  * **Default timeout**: 7-14 days (configurable)
* Closed jobs must be removed from the active discovery view.
* If a closed job reappears:

  * The system must detect and flag it as **reopened**
  * The reopened job must be surfaced prominently (treated similarly to a new posting)
  * Historical application data must be preserved and linked

### Views

* The system must provide at least two distinct graphical views:

  1. **Active Jobs**

     * open jobs not yet marked as applied
  2. **Applications**

     * jobs manually marked as applied, regardless of open/closed state

**View Capabilities:**

All views must support:

* **Sorting** by date (first seen, last seen, applied date), company name, job title
* **Filtering** by:

  * Company name
  * Job status (new, repost, existing, missing, closed, reopened)
  * Date range (first seen, last seen)
  * Application stage (if applicable)
* **Search** functionality across job titles and company names
* **Data export** to common formats (JSON, CSV) for external analysis or backup

### Application Tracking (Manual)

* The user must be able to manually:

  * mark a job as applied
  * record an application date
  * update an application stage (e.g. applied, screening, interview, rejected, offer)
  * add free-form notes or comments per application
  * record optional metadata:

    * contact person name
    * referral source
    * salary information or range
* The system must not attempt to infer application status automatically.
* **Document attachments** (e.g., resume versions, cover letters) are explicitly **out of scope** for MVP — users should manage these externally.

### Follow-up Tracking

* The system must support simple, manual follow-up tracking.
* The system must distinguish between:

  * application sent
  * follow-up sent
* Follow-up reminders must be time-based (e.g. 1 week, 2 weeks) and resettable upon follow-up.
* The system must **log follow-up history** with timestamps for each follow-up action.
* Follow-up reminders must be surfaced visually in the Applications view (e.g., visual indicator, badge count, or highlighted row).
* **Calendar integration** (e.g., .ics export, Google Calendar sync) is explicitly **out of scope** for MVP.

---

## Architecture & Hosting Constraints

* The MVP must operate without a continuously running backend server.
* The system must be runnable **locally** without requiring deployment (for development and testing).
* Data ingestion and processing must be performed via scheduled execution (e.g. CI-based jobs).
* Outputs must be stored as versioned, static data artifacts (e.g. JSON files) with **schema versioning**:

  * JSON schema must include a version field
  * Schema changes must be backward compatible OR include migration scripts
  * Breaking changes must increment the major version
* The frontend must be a statically hosted graphical interface capable of rendering and interacting with these artifacts.
* The entire system must be deployable via static hosting and repository-based automation.

---

## Constraints

* **Zero-cost constraint**: The system must be runnable using free tiers or local execution only.
* **Forkability constraint**: The repository must be self-contained and easy to clone and run independently.
* **ATS-reality constraint**: The system must degrade gracefully when faced with hostile or opaque ATS platforms.
* **Scope constraint**: Full browser automation and deep scraping are out of scope for MVP.
* **Data constraint**: Only job and application metadata may be stored; no personal or third-party user data.
* **Philosophical constraint**: The tool exists to support human judgment, not to automate hiring processes.

---

## Success Criteria

The MVP is successful if:

* The user can clearly answer:

  * "What changed since the last run?"
  * "Which roles are genuinely new versus reposted?"
* Repost noise is meaningfully reduced without hiding real opportunities.
* Closed roles disappear from discovery without erasing application history.
* Application status and follow-ups can be tracked without external tools.
* The system remains stable, explainable, and low-maintenance over time.

**Quantitative Success Metrics:**

* **Repost suppression effectiveness**: In controlled test cases with known reposts (same title, minor location/description changes), the system correctly identifies ≥90% as reposts rather than new jobs
* **Classification stability**: No uncontrolled growth in "New" classifications over time — false "New" flags should not accumulate unboundedly due to signature drift
* **System stability**: Successfully processes 50+ companies over 30 consecutive days with:
  * No systemic crashes or unrecoverable errors
  * Unsupported/failing companies do not break the entire pipeline
  * Manual intervention limited to configuration updates (not bug fixes or data repairs)
* **Performance**: Time to review new/changed jobs from all tracked companies <5 minutes per session
* **Data integrity**: No data loss or corruption due to storage layer failures:
  * All writes use atomic operations (temp file + rename)
  * Schema validation catches malformed records before persistence
  * Version conflicts are detectable and recoverable
