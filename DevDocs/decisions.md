# Decisions Log

> Append-only record of significant decisions. Never delete entries.

---

## Decision Template

```markdown
### [YYYY-MM-DD] [Short Title]

**Context:** [What situation prompted this decision?]

**Options Considered:**
1. [Option A] - [Pros/Cons]
2. [Option B] - [Pros/Cons]

**Decision:** [What we chose]

**Rationale:** [Why this option over others]

**Consequences:** [What this means for the project]
```

---

## Decisions

### [Date] Example: pytest over unittest

**Context:** Needed to choose a testing framework for the project.

**Options Considered:**
1. unittest - Built-in, no dependencies, verbose syntax
2. pytest - Requires install, cleaner syntax, better fixtures

**Decision:** Use pytest

**Rationale:** Cleaner syntax reduces test-writing friction. Fixtures and parameterization are more powerful. Industry standard for Python.

**Consequences:**
- Added pytest to dev dependencies
- Tests use `assert` statements directly
- Can use `@pytest.mark.parametrize` for edge cases

---

### [Date] [Next Decision Title]

**Context:** ...

**Options Considered:**
1. ...
2. ...

**Decision:** ...

**Rationale:** ...

**Consequences:** ...

---

<!-- Add new decisions above this line -->
