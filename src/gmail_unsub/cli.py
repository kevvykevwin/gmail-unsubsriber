"""CLI interface for Gmail Unsubscribe Agent."""

import asyncio
from pathlib import Path

import questionary
import typer
from rich.console import Console
from rich.progress import BarColumn, Progress, SpinnerColumn, TaskProgressColumn, TextColumn
from rich.table import Table

from gmail_unsub.auth.oauth import GmailAuthenticator
from gmail_unsub.config import settings
from gmail_unsub.gmail.client import GmailClient
from gmail_unsub.gmail.models import UnsubscribeStatus
from gmail_unsub.gmail.scanner import EmailScanner
from gmail_unsub.storage.history import HistoryTracker
from gmail_unsub.storage.state import StateManager
from gmail_unsub.unsubscribe.handler import UnsubscribeHandler
from gmail_unsub.utils.rate_limiter import RateLimiter

app = typer.Typer(
    name="gmail-unsub",
    help="CLI tool to unsubscribe from marketing emails in Gmail",
    no_args_is_help=True,
)
console = Console()


def get_authenticator() -> GmailAuthenticator:
    """Get the Gmail authenticator."""
    return GmailAuthenticator(
        credentials_path=settings.credentials_path,
        token_path=settings.token_path,
        scopes=settings.scopes,
    )


def get_gmail_client() -> GmailClient:
    """Get authenticated Gmail client."""
    auth = get_authenticator()
    creds = auth.get_credentials()
    rate_limiter = RateLimiter(
        requests_per_second=settings.api_requests_per_second,
        max_retries=settings.max_retries,
        base_backoff=settings.base_backoff_seconds,
    )
    return GmailClient(creds, rate_limiter)


def get_state_manager() -> StateManager:
    """Get state manager."""
    return StateManager(
        state_file=settings.state_file,
        scan_results_file=settings.scan_results_file,
    )


def get_history_tracker() -> HistoryTracker:
    """Get history tracker."""
    return HistoryTracker(history_file=settings.history_file)


@app.command()
def auth():
    """Authenticate with Gmail using OAuth 2.0."""
    authenticator = get_authenticator()

    if authenticator.is_authenticated():
        console.print("[green]Already authenticated.[/green]")
        if not typer.confirm("Re-authenticate?"):
            return

    console.print("Starting OAuth flow...")
    console.print("A browser window will open for authentication.")

    try:
        authenticator.get_credentials()
        console.print("[green]Authentication successful![/green]")
        console.print(f"Token saved to: {settings.token_path}")
    except Exception as e:
        console.print(f"[red]Authentication failed: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def scan(
    days: int = typer.Option(
        settings.scan_days_back,
        "--days",
        "-d",
        help="Days of emails to scan",
    ),
    limit: int = typer.Option(
        settings.max_emails_to_scan,
        "--limit",
        "-l",
        help="Maximum emails to scan",
    ),
):
    """Scan inbox for subscription emails."""
    try:
        client = get_gmail_client()
    except Exception as e:
        console.print(f"[red]Failed to authenticate: {e}[/red]")
        console.print("Run 'gmail-unsub auth' first.")
        raise typer.Exit(1)

    scanner = EmailScanner(client)
    state = get_state_manager()

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("Scanning inbox...", total=None)

        def update_progress(current: int, total: int):
            progress.update(task, total=total, completed=current)
            progress.update(task, description=f"Scanning messages ({current}/{total})...")

        results = scanner.scan(
            days_back=days,
            max_emails=limit,
            batch_size=settings.batch_size,
            progress_callback=update_progress,
        )

    # Save results for selection
    state.save_scan_results(results)

    # Display results
    if not results.subscriptions:
        console.print("[yellow]No subscription emails found.[/yellow]")
        return

    console.print(f"\n[green]Found {len(results.subscriptions)} subscriptions[/green]")
    console.print(f"Scanned {results.total_messages_scanned} messages from the last {days} days\n")

    _display_subscriptions_table(results.subscriptions[:20])

    if len(results.subscriptions) > 20:
        console.print(f"\n[dim]... and {len(results.subscriptions) - 20} more[/dim]")

    console.print("\nRun 'gmail-unsub select' to choose which to unsubscribe from.")


@app.command()
def select():
    """Interactive selection of subscriptions to unsubscribe."""
    state = get_state_manager()
    results = state.load_scan_results()

    if not results or not results.subscriptions:
        console.print("[yellow]No scan results found. Run 'gmail-unsub scan' first.[/yellow]")
        raise typer.Exit(1)

    # Format choices for questionary
    choices = [
        questionary.Choice(
            title=f"{sub.sender_name} ({sub.message_count} emails) [{_format_method(sub)}]",
            value=sub.sender_email,
        )
        for sub in results.subscriptions
    ]

    # Interactive selection
    selected = questionary.checkbox(
        "Select subscriptions to unsubscribe from:",
        choices=choices,
        instruction="(Use arrow keys and space to select, Enter to confirm)",
    ).ask()

    if not selected:
        console.print("[yellow]No subscriptions selected.[/yellow]")
        return

    # Get the full subscription objects
    selected_subs = [
        sub for sub in results.subscriptions if sub.sender_email in selected
    ]

    # Confirm
    console.print(f"\n[bold]Selected {len(selected_subs)} subscriptions:[/bold]")
    for sub in selected_subs:
        console.print(f"  - {sub.sender_name} <{sub.sender_email}>")

    if not typer.confirm("\nProceed with unsubscribe?"):
        console.print("[yellow]Cancelled.[/yellow]")
        return

    # Process unsubscribes
    asyncio.run(_process_unsubscribes(selected_subs))


async def _process_unsubscribes(subscriptions: list):
    """Process unsubscribe requests."""
    client = get_gmail_client()
    history = get_history_tracker()

    handler = UnsubscribeHandler(
        gmail_client=client,
        history=history,
        browser_headless=settings.browser_headless,
        browser_timeout_ms=settings.browser_timeout_ms,
        screenshots_dir=settings.data_dir / "screenshots",
    )

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("Unsubscribing...", total=len(subscriptions))

        def update_progress(current: int, total: int, email: str):
            progress.update(task, completed=current)
            progress.update(task, description=f"Processing {email}...")

        results = await handler.unsubscribe_batch(
            subscriptions,
            progress_callback=update_progress,
        )

    # Display results
    console.print("\n[bold]Results:[/bold]")
    success = 0
    failed = 0

    for result in results:
        is_success = result.status == UnsubscribeStatus.SUCCESS
        if is_success:
            success += 1
            method = result.method_used.value.replace("_", " ")
            console.print(f"  [green]✓[/green] {result.sender_email} ({method})")
        else:
            failed += 1
            console.print(f"  [red]✗[/red] {result.sender_email}: {result.error_message}")

    console.print(f"\n[bold]Summary:[/bold] {success} succeeded, {failed} failed")


@app.command()
def history(
    limit: int = typer.Option(50, "--limit", "-l", help="Number of entries to show"),
    export: Path | None = typer.Option(None, "--export", "-e", help="Export to CSV file"),
):
    """View unsubscribe history."""
    tracker = get_history_tracker()

    if export:
        tracker.export_csv(export)
        console.print(f"[green]History exported to {export}[/green]")
        return

    entries = tracker.get_history(limit=limit)

    if not entries:
        console.print("[yellow]No history found.[/yellow]")
        return

    # Stats
    stats = tracker.get_stats()
    console.print("\n[bold]Statistics:[/bold]")
    console.print(
        f"  Total: {stats['total']}, Success: {stats['success']}, Failed: {stats['failed']}"
    )
    if stats.get("success_rate"):
        console.print(f"  Success rate: {stats['success_rate']}")

    console.print(f"\n[bold]Recent activity (last {limit} entries):[/bold]\n")

    table = Table()
    table.add_column("Date", style="dim")
    table.add_column("Sender")
    table.add_column("Method")
    table.add_column("Status")

    for entry in reversed(entries[-20:]):
        status_style = "green" if entry.status == UnsubscribeStatus.SUCCESS else "red"
        table.add_row(
            entry.timestamp.strftime("%Y-%m-%d %H:%M"),
            entry.sender_email,
            entry.method_used.value.replace("_", " "),
            f"[{status_style}]{entry.status.value}[/{status_style}]",
        )

    console.print(table)


@app.command()
def undo(
    sender: str = typer.Argument(..., help="Sender email to undo spam marking for"),
):
    """Undo a spam marking (move messages back to inbox)."""
    client = get_gmail_client()
    history = get_history_tracker()

    handler = UnsubscribeHandler(
        gmail_client=client,
        history=history,
    )

    if handler.undo_spam(sender):
        console.print(f"[green]Removed {sender} from spam.[/green]")
    else:
        console.print(f"[red]Could not undo spam for {sender}.[/red]")
        console.print("Either no spam action was recorded or the messages couldn't be moved.")


@app.command()
def clear(
    what: str = typer.Argument(
        ...,
        help="What to clear: 'history', 'scan', or 'all'",
    ),
):
    """Clear stored data."""
    state = get_state_manager()
    history = get_history_tracker()

    clear_actions = {
        "history": ("Clear all history?", lambda: history.clear(), "History cleared."),
        "scan": (
            "Clear cached scan results?",
            lambda: state.clear_scan_results(),
            "Scan results cleared.",
        ),
        "all": (
            "Clear all data (history, scan results, state)?",
            lambda: (history.clear(), state.clear_scan_results(), state.clear()),
            "All data cleared.",
        ),
    }

    if what in clear_actions:
        prompt, action, success_msg = clear_actions[what]
        if typer.confirm(prompt):
            action()
            console.print(f"[green]{success_msg}[/green]")
    else:
        console.print(f"[red]Unknown option: {what}[/red]")
        console.print("Use 'history', 'scan', or 'all'")


def _display_subscriptions_table(subscriptions: list):
    """Display subscriptions in a rich table."""
    table = Table(title="Subscriptions Found")
    table.add_column("#", style="dim", width=4)
    table.add_column("Sender", style="cyan", max_width=40)
    table.add_column("Emails", justify="right", width=8)
    table.add_column("Method", style="green", width=12)
    table.add_column("Last Seen", style="dim", width=12)

    for i, sub in enumerate(subscriptions, 1):
        last_seen = sub.last_seen.strftime("%Y-%m-%d") if sub.last_seen else "?"

        table.add_row(
            str(i),
            f"{sub.sender_name}\n[dim]{sub.sender_email}[/dim]",
            str(sub.message_count),
            _format_method(sub),
            last_seen,
        )

    console.print(table)


def _format_method(sub) -> str:
    """Format the unsubscribe method for display."""
    if sub.supports_one_click:
        return "one-click"
    if sub.list_unsubscribe_mailto:
        return "mailto"
    return "browser"


if __name__ == "__main__":
    app()
