# Repository Overview

This repository is a single-owner, agent-assisted project workspace.

It is structured to clearly separate intent, execution, and historical record.
Humans and AI agents must interact with this repository according to the rules
defined below and in AGENTS.md.

---

## How to Use This Repository

This repository follows a fixed workflow:

1. **PRD.md** defines what should exist and what must not.
2. **TASKLIST.md** lists all permissible actions.
3. **CHANGELOG.md** records what has actually changed.
4. **AGENTS.md** governs how AI agents behave.

General rules:
- Do not perform work that is not represented in TASKLIST.md.
- Do not introduce new intent outside PRD.md.
- Do not explain reasoning in CHANGELOG.md.

README.md provides orientation only and is not a source of truth.

---

## Current Status
- Project phase: MVP complete with comprehensive documentation
- Completed: Phases 1-11 (Backend, Frontend, Testing, UI Polish, CI/CD, Validation, Documentation)
- Progress: 58/60 tasks complete (97%)
- Test coverage: 77 tests passing (100% repost detection accuracy)
- Remaining: 2 Phase 10 tasks (30-day stability test, formal performance docs)

Production-ready application:
- Backend: Ingestion pipeline (307 real jobs), classification engine with **100% repost detection**, temporal tracking, artifact versioning
- Frontend: Job browsing with search/filter/sort, job detail modal, application tracking, export functionality, in-app help
- CI/CD: GitHub Actions for scheduled ingestion, GitHub Pages deployment, automated snapshots
- Validation: **100% repost detection rate** (exceeds 90% PRD target), deterministic classification, full explainability
- Tests: Comprehensive unit and validation test coverage (77 tests passing)
- Documentation: Complete installation, configuration, user, architecture, and troubleshooting guides
- Deployment: Production-ready with monitoring and rollback capabilities

Refer to PRD.md for authoritative intent.
