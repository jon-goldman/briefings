"""
Publish the briefing HTML to GitHub Pages.

Pushes two files atomically:
  1. daily-briefing-YYYY-MM-DD.html  — the briefing itself
  2. index.html                       — meta-refresh redirect to today's file

Handles SHA resolution and skips unchanged content to avoid noisy commits.
"""
import asyncio
import base64
import hashlib
import os
from datetime import date

import aiohttp

GITHUB_PAT = os.environ.get("GITHUB_PAT", "")
REPO       = "jon-goldman/briefings"
API_BASE   = "https://api.github.com"

_HEADERS = lambda: {
    "Authorization":        f"Bearer {GITHUB_PAT}",
    "Accept":               "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _get_file(session: aiohttp.ClientSession, path: str) -> tuple[str | None, str | None]:
    """Return (sha, current_b64_content) for path, or (None, None) if not found."""
    async with session.get(
        f"{API_BASE}/repos/{REPO}/contents/{path}",
        headers=_HEADERS(),
        timeout=aiohttp.ClientTimeout(total=10),
    ) as r:
        if r.status == 404:
            return None, None
        r.raise_for_status()
        data = await r.json()
        return data["sha"], data.get("content", "")


async def _put_file(
    session:  aiohttp.ClientSession,
    path:     str,
    content:  str,
    message:  str,
    sha:      str | None,
) -> str:
    """PUT a file to the repo. Returns the new SHA."""
    encoded = base64.b64encode(content.encode("utf-8")).decode()
    body: dict = {"message": message, "content": encoded}
    if sha:
        body["sha"] = sha

    async with session.put(
        f"{API_BASE}/repos/{REPO}/contents/{path}",
        headers=_HEADERS(),
        json=body,
        timeout=aiohttp.ClientTimeout(total=30),
    ) as r:
        r.raise_for_status()
        data = await r.json()
        return data["content"]["sha"]


def _make_index(filename: str) -> str:
    return f"""<!DOCTYPE html>
<html><head>
<meta charset="UTF-8">
<meta http-equiv="refresh" content="0; url=./{filename}">
<title>Daily Briefing</title>
</head><body>
<p>Redirecting to <a href="./{filename}">today's briefing</a>…</p>
</body></html>"""


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

async def push_to_github(filename: str, html: str, target_date: date) -> str:
    """
    Push the briefing HTML and update index.html.
    Returns the new SHA of the briefing file.
    """
    index_html = _make_index(filename)

    async with aiohttp.ClientSession() as session:
        # Fetch current SHAs (and content for change detection) in parallel
        (briefing_sha, briefing_content), (index_sha, _) = await asyncio.gather(
            _get_file(session, filename),
            _get_file(session, "index.html"),
        )

        # Skip push if content is identical (avoids empty commits on re-runs)
        if briefing_content:
            existing = base64.b64decode(briefing_content.replace("\n", "")).decode("utf-8")
            if existing == html:
                return briefing_sha or ""

        # Push both files in parallel
        new_sha, _ = await asyncio.gather(
            _put_file(
                session, filename, html,
                f"briefing: {target_date}", briefing_sha,
            ),
            _put_file(
                session, "index.html", index_html,
                f"briefing: redirect → {filename}", index_sha,
            ),
        )

    return new_sha
