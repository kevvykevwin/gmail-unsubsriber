# Project Context

> Background information Claude needs to understand this project.
> Update when domain knowledge or constraints change.

## Project Overview

**Name:** [Project Name]
**Purpose:** [One-liner: What does this project do?]
**Owner:** [Who owns this / who to ask questions]

## Domain Knowledge

### Key Concepts

| Term | Definition |
|------|------------|
| [Domain term 1] | [What it means in this context] |
| [Domain term 2] | [What it means in this context] |

### Business Rules

- [Rule 1: e.g., "Budgets under $5 are rejected by Meta API"]
- [Rule 2: e.g., "All campaigns must have an end date"]

## Technical Context

### Stack

| Layer | Technology |
|-------|------------|
| Language | Python 3.11 |
| Testing | pytest |
| API | Meta Marketing API v18.0 |

### External Dependencies

| Service | Purpose | Docs |
|---------|---------|------|
| Meta Ads API | Campaign management | [link] |
| PostgreSQL | Data persistence | [link] |

### Environment Variables

| Variable | Purpose | Required |
|----------|---------|----------|
| `META_ACCESS_TOKEN` | API authentication | Yes |
| `DATABASE_URL` | DB connection | Yes |

## Constraints

### Technical Constraints
- [e.g., "Must run on Python 3.10+ due to match statements"]
- [e.g., "API rate limit: 200 calls/hour"]

### Business Constraints
- [e.g., "Cannot store PII in logs"]
- [e.g., "Must support multi-tenant isolation"]

## Stakeholders

| Role | Name | Cares About |
|------|------|-------------|
| Client | [Name] | [Their priorities] |
| User | [Persona] | [Their needs] |

## Related Resources

- [Link to main docs]
- [Link to API reference]
- [Link to design files]

---

## Notes

[Any other context that doesn't fit above]
