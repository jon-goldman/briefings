"""
GitHub-backed memory for briefing state.

Reads/writes memory.json in the jon-goldman/briefings repo via the Contents API.
The file stores which action items are completed or snoozed, so state persists
across briefing runs without needing a database.
"""
import asyncio
import base64
import json
import os
from datetime import date, datetime, timezone
from dataclasses import dataclass, field
from typing import Dict, Optional

import aiohttp

GITHUB_PAT  = os.environ.get("GITHUB_PAT", "")
REPO        = "jon-goldman/briefings"
MEMORY_PATH = "memory.json"
API_BASE    = "https://api.github.com"
HEADERS     = lambda: {
    "Authorization": f"Bearer {GITHUB_PAT}",
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
}


@dataclass
class Memory:
    completed:   Dict[str, str] = field(default_factory=dict)  # {item_id: "YYYY-MM-DD"}
    snoozed:     Dict[str, str] = field(default_factory=dict)  # {item_id: "YYYY-MM-DD"}
    updated_at:  Optional[str]  = None
    _sha:        Optional[str]  = field(default=None, repr=False)

    # ------------------------------------------------------------------
    # Load
    # ------------------------------------------------------------------

    @classmethod
    async def load(cls) -> "Memory":
        """Fetch memory.json from GitHub. Returns empty Memory on 404."""
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{API_BASE}/repos/{REPO}/contents/{MEMORY_PATH}",
                headers=HEADERS(),
                timeout=aiohttp.ClientTimeout(total=10),
            ) as r:
                if r.status == 404:
                    return cls()
                r.raise_for_status()
                data = await r.json()

        raw     = base64.b64decode(data["content"].replace("\n", ""))
        parsed  = json.loads(raw)
        m       = cls(
            completed  = parsed.get("completed", {}),
            snoozed    = parsed.get("snoozed", {}),
            updated_at = parsed.get("updatedAt"),
        )
        m._sha = data["sha"]
        return m

    # ------------------------------------------------------------------
    # Query helpers
    # ------------------------------------------------------------------

    def is_completed(self, item_id: str) -> bool:
        return item_id in self.completed

    def is_snoozed(self, item_id: str, today: date) -> bool:
        snooze_until = self.snoozed.get(item_id)
        if not snooze_until:
            return False
        try:
            return date.fromisoformat(snooze_until) > today
        except ValueError:
            return False

    def snooze_until(self, item_id: str) -> Optional[date]:
        raw = self.snoozed.get(item_id)
        if not raw:
            return None
        try:
            return date.fromisoformat(raw)
        except ValueError:
            return None

    # ------------------------------------------------------------------
    # Save
    # ------------------------------------------------------------------

    async def save(self) -> None:
        """Push updated memory.json to GitHub (overwrites existing file)."""
        payload = {
            "completed":  self.completed,
            "snoozed":    self.snoozed,
            "updatedAt":  datetime.now(timezone.utc).isoformat(),
        }
        encoded = base64.b64encode(
            json.dumps(payload, indent=2).encode()
        ).decode()

        body: dict = {
            "message": f"briefing: update memory {date.today()}",
            "content": encoded,
        }
        if self._sha:
            body["sha"] = self._sha

        async with aiohttp.ClientSession() as session:
            async with session.put(
                f"{API_BASE}/repos/{REPO}/contents/{MEMORY_PATH}",
                headers=HEADERS(),
                json=body,
                timeout=aiohttp.ClientTimeout(total=15),
            ) as r:
                r.raise_for_status()
                resp = await r.json()
                self._sha = resp["content"]["sha"]
