"""
Gmail inbox reader using google-api-python-client.

The Google API client is synchronous, so calls run in a thread executor
so they don't block the async event loop.
"""
import asyncio
from datetime import date, timedelta
from functools import partial
from typing import Any, Dict, List

from googleapiclient.discovery import build

from .auth import get_google_credentials

# Threads with these senders are silently skipped (promotional noise)
_SKIP_SENDERS = {
    "instantink.hpsmart.com",
    "lincolnmarket.com",
    "theretherenow@substack.com",
}


# ---------------------------------------------------------------------------
# Sync helpers (run in executor)
# ---------------------------------------------------------------------------

def _build_service():
    return build("gmail", "v1", credentials=get_google_credentials())


def _fetch_threads(query: str, max_results: int = 25) -> List[Dict[str, Any]]:
    """Return enriched thread dicts matching `query`."""
    svc     = _build_service()
    result  = svc.users().threads().list(
        userId="me", q=query, maxResults=max_results
    ).execute()

    threads = result.get("threads", [])
    enriched = []

    for t in threads:
        thread = svc.users().threads().get(
            userId="me",
            id=t["id"],
            format="metadata",
            metadataHeaders=["Subject", "From", "Date"],
        ).execute()

        messages = thread.get("messages", [])
        if not messages:
            continue

        last    = messages[-1]
        headers = {
            h["name"]: h["value"]
            for h in last.get("payload", {}).get("headers", [])
        }
        sender = headers.get("From", "")

        # Skip known noise
        if any(skip in sender for skip in _SKIP_SENDERS):
            continue

        enriched.append({
            "id":            t["id"],
            "subject":       headers.get("Subject", "(no subject)"),
            "sender":        sender,
            "date":          headers.get("Date", ""),
            "snippet":       last.get("snippet", "")[:200],
            "message_count": len(messages),
        })

    return enriched


# ---------------------------------------------------------------------------
# Public async API
# ---------------------------------------------------------------------------

async def get_inbox(today: date) -> Dict[str, List[Dict]]:
    """
    Returns {'new': [...], 'lingering': [...]}

    new      — threads received since yesterday
    lingering — threads >2 days old but within last 30 days
    """
    yesterday = (today - timedelta(days=1)).strftime("%Y/%m/%d")
    two_ago   = (today - timedelta(days=2)).strftime("%Y/%m/%d")
    thirty_ago = (today - timedelta(days=30)).strftime("%Y/%m/%d")

    new_q      = f"after:{yesterday} is:inbox -category:promotions -category:social"
    lingering_q = (
        f"is:inbox -category:promotions -category:social "
        f"before:{two_ago} after:{thirty_ago}"
    )

    loop = asyncio.get_event_loop()
    new_threads, lingering_threads = await asyncio.gather(
        loop.run_in_executor(None, partial(_fetch_threads, new_q)),
        loop.run_in_executor(None, partial(_fetch_threads, lingering_q)),
    )

    return {"new": new_threads, "lingering": lingering_threads}
