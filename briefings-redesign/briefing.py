#!/usr/bin/env python3
"""
Daily Briefing Generator
========================
Usage:
    python briefing.py                     # today's briefing, full run
    python briefing.py --date 2026-04-11   # specific date
    python briefing.py --dry-run           # render HTML to /tmp, no push/draft
    python briefing.py --skip-draft        # push but don't create Gmail draft
"""
import argparse
import asyncio
import sys
import traceback
from datetime import date, datetime
from pathlib import Path

# Load .env if present (development convenience)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from sources.memory          import Memory
from sources.weather         import get_weather
from sources.gmail           import get_inbox
from sources.calendar_source import get_events, fmt_time
from sources.notion          import get_running_list
from render                  import render_briefing
from push                    import push_to_github
from draft                   import create_gmail_draft


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _warn(label: str, exc: Exception) -> None:
    print(f"  ⚠  {label} failed: {type(exc).__name__}: {exc}", file=sys.stderr)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

async def main() -> None:
    parser = argparse.ArgumentParser(description="Generate daily briefing")
    parser.add_argument("--date",        default=str(date.today()),
                        help="Target date YYYY-MM-DD (default: today)")
    parser.add_argument("--dry-run",     action="store_true",
                        help="Render to /tmp only; skip push and draft")
    parser.add_argument("--skip-draft",  action="store_true",
                        help="Push to GitHub but skip Gmail draft")
    args = parser.parse_args()

    try:
        target_date = datetime.strptime(args.date, "%Y-%m-%d").date()
    except ValueError:
        sys.exit(f"Invalid date: {args.date}. Use YYYY-MM-DD.")

    print(f"✦ Briefing for {target_date} ({target_date.strftime('%A')})")

    # ------------------------------------------------------------------
    # Step 0: Load memory (needed before rendering)
    # ------------------------------------------------------------------
    print("  Loading memory…")
    try:
        memory = await Memory.load()
        print(f"    {len(memory.completed)} completed, {len(memory.snoozed)} snoozed")
    except Exception as e:
        _warn("memory", e)
        memory = Memory()

    # ------------------------------------------------------------------
    # Step 1–5: Gather all data sources in parallel
    # ------------------------------------------------------------------
    print("  Gathering data (weather / Gmail / Calendar / Notion)…")

    results = await asyncio.gather(
        get_weather(),
        get_inbox(target_date),
        get_events(target_date, days=3),
        get_running_list(),
        return_exceptions=True,
    )

    weather, emails, events, notion_items = results

    # Graceful degradation: replace exceptions with sensible fallbacks
    if isinstance(weather, Exception):
        _warn("weather", weather)
        weather = "Weather unavailable"

    if isinstance(emails, Exception):
        _warn("gmail", emails)
        emails = {"new": [], "lingering": []}

    if isinstance(events, Exception):
        _warn("calendar", events)
        events = []
    else:
        # Annotate events with formatted times for template + draft
        for e in events:
            e["start_fmt"] = fmt_time(e["start"])
            e["end_fmt"]   = fmt_time(e["end"])

    if isinstance(notion_items, Exception):
        _warn("notion", notion_items)
        notion_items = None

    # ------------------------------------------------------------------
    # Step 6: Render HTML
    # ------------------------------------------------------------------
    print("  Rendering HTML…")
    try:
        html = render_briefing(
            target_date  = target_date,
            memory       = memory,
            weather      = weather,
            emails       = emails,
            events       = events,
            notion_items = notion_items,
        )
    except Exception as e:
        traceback.print_exc()
        sys.exit(f"Render failed: {e}")

    filename = f"daily-briefing-{target_date}.html"

    # ------------------------------------------------------------------
    # Dry run: save locally and stop
    # ------------------------------------------------------------------
    if args.dry_run:
        out = Path("/tmp") / filename
        out.write_text(html, encoding="utf-8")
        print(f"  Dry run ✓ → {out}")
        return

    # Also write locally for inspection
    Path(filename).write_text(html, encoding="utf-8")

    # ------------------------------------------------------------------
    # Step 7: Push to GitHub Pages
    # ------------------------------------------------------------------
    print("  Pushing to GitHub Pages…")
    try:
        sha = await push_to_github(filename, html, target_date)
        print(f"    Pushed {filename} (sha: {sha[:7] if sha else 'unchanged'})")
    except Exception as e:
        _warn("github push", e)

    # ------------------------------------------------------------------
    # Step 8: Create Gmail draft
    # ------------------------------------------------------------------
    if not args.skip_draft:
        print("  Creating Gmail draft…")
        # Import focus_blocks from render context (re-derive for draft)
        from render import build_focus_blocks
        from sources.calendar_source import compute_free_windows
        free_windows = compute_free_windows(events, target_date)
        focus_blocks = build_focus_blocks(free_windows, target_date)

        try:
            draft_id = await create_gmail_draft(
                target_date, weather, events, focus_blocks
            )
            print(f"    Draft created: {draft_id}")
        except Exception as e:
            _warn("gmail draft", e)

    print(f"✓ Done — https://jon-goldman.github.io/briefings/{filename}")


if __name__ == "__main__":
    asyncio.run(main())
