# Gmail Unsubscribe Agent - Project Context

## Overview

A CLI tool that scans Gmail for subscription/marketing emails, presents them for interactive validation, and processes unsubscriptions using RFC 8058 one-click with browser automation fallback.

## Documentation Map

| Doc | Purpose | Read when... |
|-----|---------|--------------|
| `README.md` | Quick start | You want to use the tool |
| `CLAUDE.md` | Project context | You're contributing or need an overview |

## Design Philosophy

### Why This Exists

Managing email subscriptions is tedious. Most unsubscribe tools are web apps requiring email access grants to third parties. This tool runs locally, uses OAuth for secure access, and automates the unsubscribe process.

### Key Trade-offs

| Decision | Why | Why Not the Alternative |
|----------|-----|-------------------------|
| **Python** | Best Gmail API support, simple scripting | TypeScript viable but Google's Python SDK is mature |
| **OAuth 2.0** | Secure, scoped access, no password storage | App passwords less secure, IMAP has limited capabilities |
| **CLI with interactive selection** | Review before action, no accidental unsubscribes | Web UI adds complexity, fully automated is risky |
| **One-click first, browser fallback** | One-click is instant and reliable when supported | Browser-only is slower and more fragile |
| **JSON file storage** | Simple, no database dependency, human-readable | SQLite overkill for this use case |
| **Playwright for browser** | Modern, reliable, good async support | Selenium heavier, older API |

### Non-Goals

This tool explicitly does **not** aim to:
- **Run as a service** — One-time or on-demand execution only
- **Auto-unsubscribe without review** — User validation is required
- **Handle non-Gmail providers** — Gmail API specific
- **Provide a web interface** — CLI-first design

## Sensible Defaults

| Setting | Default | Rationale |
|---------|---------|-----------|
| Scan period | 90 days | Catches regular newsletters without going too far back |
| Max emails | 1000 | Prevents runaway API usage |
| Rate limit | 10 req/sec | Stays well under Gmail API quota |
| Browser mode | Headless | No visual distraction during processing |
| Unsubscribe method | One-click → mailto → browser → spam | Fastest/most reliable first |

## Architecture

```
src/gmail_unsub/
├── auth/           # OAuth 2.0 authentication
├── gmail/          # Gmail API client, scanner, models
├── unsubscribe/    # Handlers: one-click, mailto, browser
├── storage/        # State persistence, history tracking
├── utils/          # Rate limiter, patterns, errors
└── cli.py          # Typer CLI commands
```

## Tech Stack

| Component | Package | Notes |
|-----------|---------|-------|
| Gmail API | `google-api-python-client` | Official Google SDK |
| OAuth | `google-auth-oauthlib` | OAuth 2.0 flow |
| CLI | `typer` | Command structure |
| CLI formatting | `rich` | Tables, progress bars |
| Interactive | `questionary` | Checkbox selection |
| HTTP | `httpx` | Async HTTP for one-click |
| Browser | `playwright` | Automation fallback |
| Data models | `pydantic` | Validation and settings |

## Development

### Testing

#### Run tests
```bash
pytest -v
```

#### TDD workflow
1. Write/update spec in /specs/
2. Generate tests: "apply test-generator-post-build skill to [spec]"
3. Run pytest until green
4. Run security-scan before commit

#### Test conventions
- All tests in /tests/
- Naming: test_[feature].py
- Use fixtures in conftest.py for shared setup

### Quality Gates

Run before committing:

```bash
ruff check .              # Linting
ruff format --check .     # Formatting
mypy src/                 # Type checking
pytest                    # Tests
```

### Running

```bash
# Install with dev dependencies
pip install -e ".[dev]"

# Install Playwright browsers
playwright install chromium

# Run CLI
gmail-unsub --help
```

## Current Status

**In Progress**: Initial implementation
