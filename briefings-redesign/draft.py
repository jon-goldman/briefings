"""
Create a Gmail draft with a compact daily briefing summary.

The draft is sent to jongoldman93@gmail.com and links out to the full
GitHub Pages briefing. Intentionally brief: weather, timeline, focus blocks.
"""
import asyncio
import base64
from datetime import date
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from functools import partial
from typing import Dict, List

from googleapiclient.discovery import build

from sources.auth import get_google_credentials

RECIPIENT = "jongoldman93@gmail.com"
PAGES_URL = "https://jon-goldman.github.io/briefings/"


# ---------------------------------------------------------------------------
# Sync helper
# ---------------------------------------------------------------------------

def _create_draft_sync(subject: str, html_body: str) -> str:
    svc = build("gmail", "v1", credentials=get_google_credentials())

    msg = MIMEMultipart("alternative")
    msg["To"]      = RECIPIENT
    msg["Subject"] = subject
    msg.attach(MIMEText(html_body, "html"))

    raw   = base64.urlsafe_b64encode(msg.as_bytes()).decode()
    draft = svc.users().drafts().create(
        userId="me",
        body={"message": {"raw": raw}},
    ).execute()
    return draft["id"]


# ---------------------------------------------------------------------------
# Public async API
# ---------------------------------------------------------------------------

async def create_gmail_draft(
    target_date:  date,
    weather:      str,
    events:       List[Dict],
    focus_blocks: List[Dict],
) -> str:
    """Build and create the Gmail draft. Returns draft ID."""
    weekday   = target_date.strftime("%A")
    month_day = target_date.strftime("%B %-d")
    subject   = f"📋 {weekday} Briefing — {month_day}"

    today_str    = str(target_date)
    today_events = [e for e in events if e.get("date") == today_str]

    events_li = "".join(
        f"<li><strong>{e.get('start_fmt', '')}–{e.get('end_fmt', '')}</strong> "
        f"{e['summary']}"
        f"{' · ' + e['location'] if e.get('location') else ''}</li>"
        for e in today_events
    ) or "<li>No events today.</li>"

    focus_li = "".join(
        f"<li><strong>{b['time']}</strong> — {b['task']}</li>"
        for b in focus_blocks
    ) or "<li>No focus blocks.</li>"

    html_body = f"""<div style="font-family:sans-serif;line-height:1.6;max-width:600px;color:#222">
<h2 style="margin:0 0 4px;font-size:18px">📋 {weekday} Briefing — {month_day}</h2>
<p style="margin:0 0 16px;color:#666;font-size:14px">{weather}</p>

<h3 style="margin:0 0 6px;font-size:14px;text-transform:uppercase;letter-spacing:.05em;color:#888">Today</h3>
<ul style="margin:0 0 16px;padding-left:20px;font-size:14px">{events_li}</ul>

<h3 style="margin:0 0 6px;font-size:14px;text-transform:uppercase;letter-spacing:.05em;color:#888">Focus Blocks</h3>
<ul style="margin:0 0 16px;padding-left:20px;font-size:14px">{focus_li}</ul>

<p style="margin:0;font-size:14px">
  <a href="{PAGES_URL}" style="color:#0066cc">View full briefing →</a>
</p>
</div>"""

    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        None, partial(_create_draft_sync, subject, html_body)
    )
