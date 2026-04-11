#!/usr/bin/env python3
"""
One-time Google OAuth setup.

Run this once to obtain a refresh token, then add the three values
it prints to your .env file. You never need to run it again unless
you revoke access or rotate credentials.

Prerequisites:
  1. Go to https://console.cloud.google.com/apis/credentials
  2. Create an OAuth 2.0 Client ID (Desktop app type)
  3. Download the JSON and save it as client_secret.json in this directory
  4. Enable Gmail API and Google Calendar API for your project
  5. Run: python setup_auth.py
"""
import json
import sys
from pathlib import Path

try:
    from google_auth_oauthlib.flow import InstalledAppFlow
except ImportError:
    sys.exit(
        "Missing dependency. Run: pip install google-auth-oauthlib"
    )

SCOPES = [
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/calendar.readonly",
]

CLIENT_SECRET_FILE = Path("client_secret.json")


def main() -> None:
    if not CLIENT_SECRET_FILE.exists():
        sys.exit(
            f"client_secret.json not found.\n"
            f"Download it from https://console.cloud.google.com/apis/credentials "
            f"and place it in this directory."
        )

    flow  = InstalledAppFlow.from_client_secrets_file(str(CLIENT_SECRET_FILE), SCOPES)
    creds = flow.run_local_server(port=0)

    client_info = json.loads(CLIENT_SECRET_FILE.read_text())
    installed   = client_info.get("installed", client_info.get("web", {}))

    print("\n✓ Auth complete. Add these to your .env file:\n")
    print(f'GOOGLE_CLIENT_ID="{installed["client_id"]}"')
    print(f'GOOGLE_CLIENT_SECRET="{installed["client_secret"]}"')
    print(f'GOOGLE_REFRESH_TOKEN="{creds.refresh_token}"')
    print()
    print("Then run: python briefing.py --dry-run  to test.")


if __name__ == "__main__":
    main()
