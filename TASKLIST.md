# Task List

This file is the authoritative execution ledger.

All actions performed by humans or AI agents must correspond
to an explicit task listed here.

Agents may not infer, bundle, or silently execute work.

---

## Summary

**Total Tasks:** 60
**Completed:** 58 (97%)
**Pending:** 2 (3%)

---

## Pending

### Phase 10: Testing & Validation

- [x] TASK-050: Create test dataset with known repost scenarios
- [x] TASK-051: Validate repost suppression effectiveness (≥90% in controlled test cases) - **RESULT: 100%**
- [x] TASK-052: Monitor classification stability (no unbounded growth in false "New" flags) - **RESULT: Stable, deterministic**
- [ ] TASK-053: Perform 30-day stability test (50+ companies, no crashes, isolated failures, config-only intervention)
- [ ] TASK-054: Validate performance (review time <5 minutes) - **PARTIAL: Validated at ~2-3 minutes, needs documentation**
- [ ] TASK-055: Verify data integrity (atomic writes, schema validation, conflict detection) - **PARTIAL: Verified in code, needs formal test**

### Phase 11: Documentation

- [x] TASK-056: Write installation and setup guide
- [x] TASK-057: Document company configuration process
- [x] TASK-058: Create user guide for views and tracking
- [x] TASK-059: Document architecture and design decisions
- [x] TASK-060: Create troubleshooting guide

---

## Completed

### Phase 1: Project Setup & Core Architecture

- [x] TASK-000: Enhanced PRD.md with detailed requirements and success metrics
- [x] TASK-001: Define project technology stack and architecture decisions
- [x] TASK-002: Create project directory structure (ingestion, processing, frontend, data, config)
- [x] TASK-003: Define JSON data schema with versioning for job records
- [x] TASK-004: Create configuration schema for company watchlist
- [x] TASK-005: Set up local development environment setup documentation

### Phase 2: Data Ingestion Infrastructure

- [x] TASK-006: Implement base ingestion framework with scheduling support
- [x] TASK-007: Add respectful crawling controls (delays, user-agent, rate limiting)
- [x] TASK-008: Implement error handling and retry logic for ingestion
- [x] TASK-009: Create logging system for ingestion activities
- [x] TASK-010: Implement URL validation for company sources
- [x] TASK-011: Create company configuration loader and validator

### Phase 3: ATS Adapters (Initial Set)

- [x] TASK-012: Research and document 3-5 common ATS platforms for MVP
- [x] TASK-013: Implement adapter interface/base class
- [x] TASK-014: Create adapter for Greenhouse
- [x] TASK-015: Create adapter for Lever
- [x] TASK-016: Create adapter for Workday

### Phase 4: Job Classification & Temporal Tracking

- [x] TASK-017: Implement job signature normalization logic (case, whitespace, abbreviations)
- [x] TASK-018: Create fuzzy matching system with configurable threshold
- [x] TASK-019: Implement job classification engine (New/Repost/Existing)
- [x] TASK-020: Add explainability metadata to classification decisions
- [x] TASK-021: Implement temporal tracking (first_seen, last_seen, observations)
- [x] TASK-022: Create job lifecycle state machine (active/missing/closed/reopened)
- [x] TASK-023: Implement configurable timeout for closed job detection

### Phase 5: Data Storage & Persistence

- [x] TASK-024: Implement JSON data serialization with schema versioning
- [x] TASK-025: Create data retention and archival logic
- [x] TASK-026: Implement data export functionality (JSON, CSV)
- [x] TASK-027: Create data migration utility for schema changes

### Phase 6: Frontend - Core Views

- [x] TASK-028: Set up static frontend framework (HTML/CSS/JS or framework TBD)
- [x] TASK-029: Implement data loader for JSON artifacts
- [x] TASK-030: Create "Active Jobs" view with job listing
- [x] TASK-031: Create "Applications" view with application listing
- [x] TASK-032: Implement sorting functionality (date, company, title)
- [x] TASK-033: Implement filtering (company, status, date range)
- [x] TASK-034: Implement search across titles and companies

### Phase 7: Application & Follow-up Tracking

- [x] TASK-035: Implement manual application marking functionality
- [x] TASK-036: Create application metadata capture (date, stage, notes)
- [x] TASK-037: Add optional metadata fields (contact, referral, salary)
- [x] TASK-038: Implement follow-up tracking with timestamp logging
- [x] TASK-039: Create visual follow-up reminder indicators
- [x] TASK-040: Implement follow-up history display

### Phase 8: UI/UX Polish

- [x] TASK-041: Design and implement responsive layout
- [x] TASK-042: Add visual indicators for job states (new, repost, reopened, etc.)
- [x] TASK-043: Implement job detail view/modal
- [x] TASK-044: Add data export UI controls
- [x] TASK-045: Create help/documentation page

### Phase 9: CI/CD & Deployment

- [x] TASK-046: Create GitHub Actions workflow for scheduled ingestion
- [x] TASK-047: Set up static hosting configuration (GitHub Pages or alternative)
- [x] TASK-048: Implement artifact versioning and storage strategy
- [x] TASK-049: Create deployment documentation
