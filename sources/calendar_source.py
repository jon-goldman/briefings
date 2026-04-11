"""
Google Calendar reader.

Fetches events for a date window, skips declined invites,
and returns structured dicts the renderer can work with.
"""
import asyncio
from datetime import date, datetime, timedelta
from functools import partial
from typing import Any, Dict, List, Optional

from googleapiclient.discovery import build

from .auth import get_google_credentials

_TZ_OFFSET = "-04:00"  # EDT; update to -05:00 after DST ends


def _build_service():
    return build("calendar", "v3", credentials=get_google_credentials())


def _fetch_events(time_min: str, time_max: str) -> List[Dict[str, Any]]:
    svc = _build_service()
    result = svc.events().list(
        calendarId="primary",
        timeMin=time_min,
        timeMax=time_max,
        singleEvents=True,
        orderBy="startTime",
        maxResults=100,
    ).execute()

    events = []
    for e in result.get("items", []):
        # Skip events the user explicitly declined
        declined = any(
            att.get("self") and att.get("responseStatus") == "declined"
            for att in e.get("attendees", [])
        )
        if declined:
            continue

        start_raw = e.get("start", {})
        end_raw   = e.get("end", {})
        all_day   = "date" in start_raw and "dateTime" not in start_raw

        start_str = start_raw.get("dateTime") or start_raw.get("date", "")
        end_str   = end_raw.get("dateTime") or end_raw.get("date", "")

        events.append({
            "id":          e["id"],
            "summary":     e.get("summary", "(no title)"),
            "start":       start_str,
            "end":         end_str,
            "date":        start_str[:10],
            "location":    e.get("location", ""),
            "description": e.get("description", ""),
            "all_day":     all_day,
        })

    return events


# ---------------------------------------------------------------------------
# Public async API
# ---------------------------------------------------------------------------

async def get_events(today: date, days: int = 3) -> List[Dict[str, Any]]:
    """Fetch calendar events from today through today+days (inclusive)."""
    time_min = f"{today}T00:00:00{_TZ_OFFSET}"
    time_max = f"{today + timedelta(days=days)}T23:59:59{_TZ_OFFSET}"

    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        None, partial(_fetch_events, time_min, time_max)
    )


def fmt_time(dt_str: str) -> str:
    """'2026-04-10T11:25:00-04:00' → '11:25am'"""
    if not dt_str or "T" not in dt_str:
        return dt_str or ""
    try:
        dt = datetime.fromisoformat(dt_str)
        return dt.strftime("%-I:%M%p").lower().replace(":00", "")
    except ValueError:
        return dt_str


def compute_free_windows(events: List[Dict], today: date,
                         day_start: int = 8, day_end: int = 22) -> List[Dict]:
    """
    Return list of free windows >30 min for `today`.
    Each window: {'start': 'HH:MM', 'end': 'HH:MM', 'minutes': int}
    """
    today_str  = str(today)
    today_evts = [e for e in events if e["date"] == today_str and not e["all_day"]]

    # Convert to (start_min, end_min) pairs relative to midnight
    busy: List[tuple] = []
    for e in today_evts:
        try:
            s = datetime.fromisoformat(e["start"])
            n = datetime.fromisoformat(e["end"])
            busy.append((s.hour * 60 + s.minute, n.hour * 60 + n.minute))
        except ValueError:
            continue

    busy.sort()

    # Merge overlaps
    merged: List[tuple] = []
    for s, e in busy:
        if merged and s <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], e))
        else:
            merged.append((s, e))

    # Find gaps
    windows = []
    cursor  = day_start * 60
    end_of_day = day_end * 60

    for s, e in merged:
        if s > cursor and s - cursor >= 30:
            windows.append({
                "start":   f"{cursor // 60:02d}:{cursor % 60:02d}",
                "end":     f"{s // 60:02d}:{s % 60:02d}",
                "minutes": s - cursor,
            })
        cursor = max(cursor, e)

    if end_of_day > cursor and end_of_day - cursor >= 30:
        windows.append({
            "start":   f"{cursor // 60:02d}:{cursor % 60:02d}",
            "end":     f"{end_of_day // 60:02d}:{end_of_day % 60:02d}",
            "minutes": end_of_day - cursor,
        })

    return windows
