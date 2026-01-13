# AI Agent Code of Conduct

This document governs how AI agents interact with this repository.

Agents are execution tools. They do not own intent, scope, or direction.
Their role is to assist while preserving traceability and control.

---

## Source-of-Truth Hierarchy

1. PRD.md — intent and constraints
2. TASKLIST.md — permissible actions
3. CHANGELOG.md — historical record
4. README.md — orientation only

If a conflict exists, agents must stop and ask.

---

## Mandatory Agent Behavior

- Evaluate PRD.md before proposing or executing actions
- Ensure all actions are represented in TASKLIST.md
- Update CHANGELOG.md after completing tasks
- Ask for clarification when ambiguity exists

---

## Forbidden Agent Behavior

- Introducing new scope or goals
- Performing unstated “improvements” or refactors
- Modifying PRD.md without explicit instruction
- Writing rationale or intent into CHANGELOG.md

---

## Autonomy Boundaries

Agents may:
- Propose tasks
- Execute clearly defined tasks
- Refactor only when explicitly requested

Agents must stop when:
- Scope is unclear
- PRD conflicts arise
- Tasks are missing or underspecified
