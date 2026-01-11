# Progress Log

> This file is updated frequently. Read this FIRST after any context break.

## Current Status

**Working on:** [Brief description of current task]
**Test state:** X/Y passing
**Blocked:** Yes/No

## Last Action

[What was just completed or attempted]

```
[Any relevant output, error message, or result]
```

## Next Steps

1. [ ] [Immediate next task]
2. [ ] [Following task]
3. [ ] [Then this]

## Session Log

### [Date/Time or Session ID]

**Started:** [What state was the project in]
**Goal:** [What we aimed to accomplish]
**Outcome:** [What actually happened]

Key changes:
- [Change 1]
- [Change 2]

Commits:
- `abc123` - [commit message]

---

### [Previous Session]

**Started:** ...
**Goal:** ...
**Outcome:** ...

---

## Blockers / Open Questions

| Issue | Status | Notes |
|-------|--------|-------|
| [Blocker 1] | Blocked | [Who/what can unblock] |
| [Question 1] | Investigating | [Current hypothesis] |

## Failed Approaches

> Document what didn't work so we don't retry it

| Approach | Why It Failed | Date |
|----------|---------------|------|
| [Approach 1] | [Reason] | YYYY-MM-DD |

---

## Quick Recovery

If resuming and this file seems stale:

```bash
# Check actual test state
pytest --tb=short -q

# Check uncommitted work
git status
git diff --stat

# Recent commits
git log --oneline -5
```
