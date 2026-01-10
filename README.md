# Gmail Unsubscribe Agent

A CLI tool that scans your Gmail inbox for subscription/marketing emails, presents them for interactive review, and helps you unsubscribe using RFC 8058 one-click, mailto links, or browser automation.

## Features

- **Smart Scanning**: Automatically detects subscription emails using List-Unsubscribe headers
- **Interactive Selection**: Review and choose which subscriptions to remove
- **Multiple Unsubscribe Methods**:
  - RFC 8058 one-click POST (fastest, most reliable)
  - mailto: email-based unsubscribe
  - Playwright browser automation for complex pages
  - Mark as spam (fallback)
- **History Tracking**: Full audit log of all actions
- **Rate Limiting**: Respects Gmail API quotas

## Installation

```bash
# Clone the repository
cd /path/to/gmail-unscriber

# Install with pip
pip install -e .

# Install Playwright browsers (for browser automation)
playwright install chromium
```

## Google Cloud Setup

Before using, you need to set up OAuth credentials:

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project (or select existing)
3. Enable the Gmail API
4. Configure OAuth consent screen:
   - User Type: External
   - Add scopes: `gmail.readonly`, `gmail.modify`, `gmail.send`
5. Create OAuth 2.0 Client ID:
   - Application type: Desktop app
6. Download the credentials JSON file
7. Save as `credentials.json` in the project root

## Usage

### 1. Authenticate

```bash
gmail-unsub auth
```

This opens a browser for OAuth consent. Your token is saved locally.

### 2. Scan Your Inbox

```bash
# Scan last 90 days (default)
gmail-unsub scan

# Scan last 30 days, limit to 500 emails
gmail-unsub scan --days 30 --limit 500
```

### 3. Select & Unsubscribe

```bash
gmail-unsub select
```

Use arrow keys and space to select subscriptions, then confirm.

### 4. View History

```bash
# View recent activity
gmail-unsub history

# Export to CSV
gmail-unsub history --export history.csv
```

### 5. Undo Spam Marking

```bash
gmail-unsub undo sender@example.com
```

## Commands

| Command | Description |
|---------|-------------|
| `gmail-unsub auth` | Authenticate with Gmail |
| `gmail-unsub scan` | Scan inbox for subscriptions |
| `gmail-unsub select` | Interactive unsubscribe selection |
| `gmail-unsub history` | View action history |
| `gmail-unsub undo <email>` | Undo spam marking |
| `gmail-unsub clear <what>` | Clear data (history/scan/all) |

## Configuration

Copy `.env.example` to `.env` to customize settings:

```bash
# Scanning
GMAIL_UNSUB_MAX_EMAILS_TO_SCAN=1000
GMAIL_UNSUB_SCAN_DAYS_BACK=90

# Rate limiting
GMAIL_UNSUB_API_REQUESTS_PER_SECOND=10

# Browser automation
GMAIL_UNSUB_BROWSER_HEADLESS=true
```

## How It Works

1. **Scan**: Queries Gmail for emails in Promotions/Updates categories with List-Unsubscribe headers
2. **Aggregate**: Groups by sender, identifies best unsubscribe method
3. **Select**: Interactive CLI to review and choose subscriptions
4. **Unsubscribe**: Tries methods in order:
   - RFC 8058 one-click POST (instant)
   - Send unsubscribe email via mailto:
   - Browser automation for complex pages
   - Mark as spam (last resort)

## Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Lint
ruff check .

# Type check
mypy src/
```

## License

MIT
