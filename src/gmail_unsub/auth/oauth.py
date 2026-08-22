"""Gmail OAuth 2.0 authentication."""

from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

from gmail_unsub.utils.errors import AuthenticationError


class GmailAuthenticator:
    """Handle Gmail OAuth 2.0 authentication flow."""

    def __init__(
        self,
        credentials_path: Path,
        token_path: Path,
        scopes: list[str],
    ) -> None:
        self.credentials_path = credentials_path
        self.token_path = token_path
        self.scopes = scopes

    def get_credentials(self) -> Credentials:
        """Get valid credentials, refreshing or re-authenticating as needed."""
        creds = None

        # Load existing token
        if self.token_path.exists():
            try:
                creds = Credentials.from_authorized_user_file(
                    str(self.token_path),
                    self.scopes,
                )
            except Exception as e:
                raise AuthenticationError(f"Failed to load token: {e}") from e

        # Refresh or get new credentials
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                except Exception:
                    # Token refresh failed, need to re-authenticate
                    creds = self._run_oauth_flow()
            else:
                creds = self._run_oauth_flow()

            # Save the credentials
            self._save_token(creds)

        return creds

    def _run_oauth_flow(self) -> Credentials:
        """Run the OAuth flow to get new credentials."""
        if not self.credentials_path.exists():
            raise AuthenticationError(
                f"Credentials file not found: {self.credentials_path}\n"
                "Please download OAuth credentials from Google Cloud Console:\n"
                "1. Go to https://console.cloud.google.com/\n"
                "2. Create/select a project and enable Gmail API\n"
                "3. Create OAuth 2.0 Client ID (Desktop App type)\n"
                "4. Download and save as credentials.json"
            )

        try:
            flow = InstalledAppFlow.from_client_secrets_file(
                str(self.credentials_path),
                self.scopes,
            )
            creds = flow.run_local_server(port=0)
            return creds
        except Exception as e:
            raise AuthenticationError(f"OAuth flow failed: {e}") from e

    def _save_token(self, creds: Credentials) -> None:
        """Save credentials to token file with restrictive permissions."""
        self.token_path.parent.mkdir(parents=True, exist_ok=True)
        self.token_path.write_text(creds.to_json())
        # Set restrictive permissions (owner read/write only)
        self.token_path.chmod(0o600)

    def is_authenticated(self) -> bool:
        """Check if valid credentials exist."""
        if not self.token_path.exists():
            return False
        try:
            creds = Credentials.from_authorized_user_file(
                str(self.token_path),
                self.scopes,
            )
            # Valid if token is current OR if it can be refreshed
            return creds.valid or (creds.expired and creds.refresh_token is not None)
        except Exception:
            return False

    def revoke(self) -> None:
        """Revoke current credentials and delete token file."""
        if self.token_path.exists():
            self.token_path.unlink()
