"""
Notion running list reader via direct REST API.

Paginates through all children of the Running List page and returns
the text of every unchecked to-do block.
"""
import os
from typing import List, Optional

import aiohttp

NOTION_API_KEY    = os.environ.get("NOTION_API_KEY", "")
RUNNING_LIST_ID   = "337f38f0-e327-8066-8ab2-cbd3e3102abf"
NOTION_VERSION    = "2022-06-28"


async def get_running_list(page_id: str = RUNNING_LIST_ID) -> Optional[List[str]]:
    """
    Returns list of unchecked to-do item strings.
    Returns None on auth error (missing key), raises on other failures.
    """
    if not NOTION_API_KEY:
        return None

    headers = {
        "Authorization":  f"Bearer {NOTION_API_KEY}",
        "Notion-Version": NOTION_VERSION,
        "Content-Type":   "application/json",
    }

    items: List[str] = []
    cursor: Optional[str] = None

    async with aiohttp.ClientSession() as session:
        while True:
            params: dict = {"page_size": 100}
            if cursor:
                params["start_cursor"] = cursor

            async with session.get(
                f"https://api.notion.com/v1/blocks/{page_id}/children",
                headers=headers,
                params=params,
                timeout=aiohttp.ClientTimeout(total=15),
            ) as r:
                r.raise_for_status()
                data = await r.json()

            for block in data.get("results", []):
                if block.get("type") != "to_do":
                    continue
                todo = block["to_do"]
                if todo.get("checked", False):
                    continue
                text = "".join(
                    rt.get("plain_text", "")
                    for rt in todo.get("rich_text", [])
                ).strip()
                if text:
                    items.append(text)

            if not data.get("has_more"):
                break
            cursor = data.get("next_cursor")

    return items
