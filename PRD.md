# Product Requirements Document (PRD)

This document defines the intent, scope, and constraints of the project.

AI agents must evaluate all proposed actions against this document
before execution. If an action contradicts or extends this document,
it must be flagged and not executed silently.

PRD.md may only be modified with explicit intent-level instructions.

---

## Problem Statement

For specialized roles in R&D, process engineering, and manufacturing-adjacent domains, traditional job search workflows based on keyword queries across aggregators are inefficient and cognitively expensive. Roles are inconsistently titled, short-lived, or quietly reposted, and most platforms are stateless: they do not answer the user’s real question — *what changed since I last checked?*

Additionally, target employers use heterogeneous Applicant Tracking Systems (ATS). Some provide clean, structured endpoints; others regenerate job IDs, temporarily remove postings, or aggressively obscure structure. This makes naive “new job” detection unreliable and prone to false positives.

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
* Company configuration must explicitly separate:

  * Company name
  * Source type (ATS / semi-structured page)
  * One or more source URLs
* Each company must be associated with exactly one ingestion strategy.

### Job Ingestion (Scheduled)

* Job ingestion must run periodically as a scheduled task.
* Ingestion must fetch the *current observable set* of job postings per company.
* The system must tolerate:

  * unstable or regenerated job IDs
  * temporary disappearance of postings
* Ingestion must produce structured records containing at minimum:

  * company
  * job title
  * location
  * job URL
  * source identifier (if available)

### Temporal Tracking

* For each job record, the system must track:

  * `first_seen` timestamp
  * `last_seen` timestamp
* `last_seen` must be updated on every ingestion cycle in which the job is observed.

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

Classification must be deterministic and explainable.

### Job Lifecycle Handling

* If a previously observed job is not seen in a given ingestion run:

  * it must remain active but flagged as "missing" until a configurable timeout.
* If a job is not seen for longer than the timeout window:

  * it must be marked as **closed**.
* Closed jobs must be removed from the active discovery view.

### Views

* The system must provide at least two distinct graphical views:

  1. **Active Jobs**

     * open jobs not yet marked as applied
  2. **Applications**

     * jobs manually marked as applied, regardless of open/closed state

### Application Tracking (Manual)

* The user must be able to manually:

  * mark a job as applied
  * record an application date
  * update an application stage (e.g. applied, screening, interview, rejected, offer)
* The system must not attempt to infer application status automatically.

### Follow-up Tracking

* The system must support simple, manual follow-up tracking.
* The system must distinguish between:

  * application sent
  * follow-up sent
* Follow-up reminders must be time-based (e.g. 1 week, 2 weeks) and resettable upon follow-up.

---

## Architecture & Hosting Constraints

* The MVP must operate without a continuously running backend server.
* Data ingestion and processing must be performed via scheduled execution (e.g. CI-based jobs).
* Outputs must be stored as versioned, static data artifacts (e.g. JSON files).
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

  * “What changed since the last run?”
  * “Which roles are genuinely new versus reposted?”
* Repost noise is meaningfully reduced without hiding real opportunities.
* Closed roles disappear from discovery without erasing application history.
* Application status and follow-ups can be tracked without external tools.
* The system remains stable, explainable, and low-maintenance over time.
