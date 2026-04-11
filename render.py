"""
Render the daily briefing HTML from gathered data.

Uses Jinja2 with template.html. All data-shaping logic lives here so that
template.html stays readable markup.
"""
from __future__ import annotations

from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

from jinja2 import Environment, FileSystemLoader

from data.items import ACTION_ITEMS, COURSES, RECURRING_IDS
from sources.calendar_source import fmt_time, compute_free_windows
from sources.memory import Memory

_TEMPLATE_DIR = Path(__file__).parent
_env = Environment(loader=FileSystemLoader(str(_TEMPLATE_DIR)), autoescape=True)

DAYS_AHEAD_RADAR = 14  # "On the Radar" looks this far out


# ---------------------------------------------------------------------------
# Focus block generation
# ---------------------------------------------------------------------------

def _upcoming_readings(today: date, days: int = 7) -> List[Dict]:
    """Return readings due in the next `days` days, sorted by urgency."""
    upcoming = []
    for course in COURSES:
        for date_str, readings in course.get("readings", {}).items():
            class_date = date.fromisoformat(date_str)
            if today < class_date <= today + timedelta(days=days):
                days_away = (class_date - today).days
                total_min = sum(r["minutes"] for r in readings if r.get("minutes"))
                for r in readings:
                    upcoming.append({
                        "course":     course["name"],
                        "class_date": class_date,
                        "days_away":  days_away,
                        "text":       r["text"],
                        "minutes":    r.get("minutes"),
                        "total_set_minutes": total_min,
                    })
    upcoming.sort(key=lambda x: x["days_away"])
    return upcoming


def _upcoming_deadlines(today: date, days: int = DAYS_AHEAD_RADAR) -> List[Dict]:
    deadlines = []
    for course in COURSES:
        for dl in course.get("deadlines", []):
            dl_date = date.fromisoformat(dl["date"])
            if today <= dl_date <= today + timedelta(days=days):
                deadlines.append({
                    "course":    course["name"],
                    "date":      dl_date,
                    "days_away": (dl_date - today).days,
                    "label":     dl["label"],
                })
    deadlines.sort(key=lambda x: x["days_away"])
    return deadlines


def build_focus_blocks(free_windows: List[Dict], today: date) -> List[Dict]:
    """
    Match the top-priority readings/deadlines to the available free windows.
    Returns up to 3 focus block dicts with 'time', 'task', 'duration_label'.
    """
    readings  = _upcoming_readings(today, days=7)
    deadlines = _upcoming_deadlines(today, days=5)

    # Build a priority queue: readings first, then near deadlines
    tasks = []
    seen_courses = set()
    for r in readings:
        if r["course"] not in seen_courses:
            seen_courses.add(r["course"])
            mins = r["minutes"]
            mins_label = f"~{mins} min" if mins else "time unknown"
            tasks.append({
                "label":    f"{r['course']}: {r['text']} ({mins_label})",
                "minutes":  mins or 60,
                "urgency":  "reading",
            })

    for dl in deadlines:
        if dl["days_away"] <= 5:
            tasks.append({
                "label":    f"{dl['course']}: {dl['label']}",
                "minutes":  90,
                "urgency":  "deadline",
            })

    blocks = []
    task_idx = 0
    for window in free_windows:
        if task_idx >= len(tasks) or len(blocks) >= 3:
            break
        task = tasks[task_idx]
        # Only assign if window is long enough (at least task duration or 30 min)
        alloc = min(task["minutes"], window["minutes"])
        if alloc < 25:
            continue
        blocks.append({
            "time":           f"{window['start']}–{window['end']}",
            "task":           task["label"],
            "duration_label": f"{alloc} min",
        })
        task_idx += 1

    return blocks


# ---------------------------------------------------------------------------
# Action item grouping
# ---------------------------------------------------------------------------

def group_action_items(memory: Memory, today: date,
                       notion_items: Optional[List[str]]) -> Dict[str, List[Dict]]:
    """
    Returns dict of groups:
      'today'    — immediate/time-sensitive
      'upcoming' — deadline within 10 days
      'errand'   — everything else active
      'snoozed'  — hidden until snooze date passes
      'done'     — completed (pre-checked, struck-through)
    """
    groups: Dict[str, List[Dict]] = {
        "today":    [],
        "upcoming": [],
        "errand":   [],
        "snoozed":  [],
        "done":     [],
    }

    # Merge Notion items into ACTION_ITEMS (deduped by label)
    known_labels = {it["label"].lower() for it in ACTION_ITEMS}
    extra_items  = []
    if notion_items:
        for text in notion_items:
            if text.lower() not in known_labels:
                slug = text.lower().replace(" ", "-").replace("/", "-")[:40]
                extra_items.append({"id": f"notion-{slug}", "label": text, "group": "errand"})

    all_items = ACTION_ITEMS + extra_items

    for item in all_items:
        item_id  = item["id"]
        is_recurring = item_id in RECURRING_IDS

        if memory.is_completed(item_id) and not is_recurring:
            groups["done"].append({**item, "checked": True})
            continue

        if memory.is_snoozed(item_id, today):
            snooze_dt = memory.snooze_until(item_id)
            groups["snoozed"].append({
                **item,
                "snooze_until": snooze_dt.strftime("%-m/%-d") if snooze_dt else "",
            })
            continue

        # Assign active items to groups
        if item["group"] == "deadline":
            # Check if it's critically close (≤10 days)
            groups["upcoming"].append(item)
        elif item_id in {"facebook-link", "ikar-instagram"}:
            groups["today"].append(item)
        else:
            groups["errand"].append(item)

    return groups


# ---------------------------------------------------------------------------
# Radar section
# ---------------------------------------------------------------------------

def build_radar(today: date) -> List[Dict]:
    """
    Return upcoming class sessions + deadlines within DAYS_AHEAD_RADAR days,
    skipping today (already in timeline).
    """
    radar = []
    seen  = set()

    for course in COURSES:
        no_class = set(course.get("no_class", []))
        days_set = course.get("days", [])

        # Upcoming class sessions
        for offset in range(1, DAYS_AHEAD_RADAR + 1):
            d = today + timedelta(days=offset)
            d_str = str(d)
            if d_str in no_class:
                continue
            if d.strftime("%A") not in days_set:
                continue

            readings = course["readings"].get(d_str, [])
            reading_str = ""
            if readings:
                total_min = sum(r["minutes"] for r in readings if r.get("minutes"))
                texts = [r["text"] for r in readings]
                reading_str = ", ".join(texts)
                if total_min:
                    reading_str += f" (~{total_min // 60}h {total_min % 60}m total)" if total_min >= 60 else f" (~{total_min} min)"

            key = (course["name"], d_str)
            if key not in seen:
                seen.add(key)
                radar.append({
                    "date":     d,
                    "label":    f"{course['name']} — {d.strftime('%a %-m/%-d')}, {course['time']}",
                    "reading":  reading_str,
                    "location": course.get("location", ""),
                    "type":     "class",
                })

        # Deadlines
        for dl in course.get("deadlines", []):
            dl_date = date.fromisoformat(dl["date"])
            if today < dl_date <= today + timedelta(days=DAYS_AHEAD_RADAR):
                key = (course["name"], dl["date"], "deadline")
                if key not in seen:
                    seen.add(key)
                    radar.append({
                        "date":    dl_date,
                        "label":   f"{course['name']}: {dl['label']}",
                        "reading": "",
                        "type":    "deadline",
                    })

    radar.sort(key=lambda x: x["date"])
    return radar


# ---------------------------------------------------------------------------
# Main render function
# ---------------------------------------------------------------------------

def render_briefing(
    target_date:  date,
    memory:       Memory,
    weather:      str,
    emails:       Dict[str, List[Dict]],
    events:       List[Dict],
    notion_items: Optional[List[str]],
    improvement:  str = "",
) -> str:
    weekday    = target_date.strftime("%A")
    month_day  = target_date.strftime("%B %-d, %Y")
    filename   = f"daily-briefing-{target_date}.html"

    # Calendar
    today_str     = str(target_date)
    today_events  = [e for e in events if e["date"] == today_str]
    later_events  = [e for e in events if e["date"] > today_str]
    free_windows  = compute_free_windows(events, target_date)
    focus_blocks  = build_focus_blocks(free_windows, target_date)

    # Format event times for template
    for e in events:
        e["start_fmt"] = fmt_time(e["start"])
        e["end_fmt"]   = fmt_time(e["end"])

    # Action items
    action_groups = group_action_items(memory, target_date, notion_items)

    # Radar
    radar = build_radar(target_date)

    # Improvement idea (default if not provided)
    if not improvement:
        improvement = (
            "Consider adding a 'Reading Load' mini-chart to the On the Radar section "
            "showing estimated hours of reading by day for the next two weeks. "
            "This would make it much easier to spot overloaded days and front-load lighter weeks."
        )

    template = _env.get_template("template.html")
    return template.render(
        weekday        = weekday,
        month_day      = month_day,
        target_date    = target_date,
        filename       = filename,
        weather        = weather,
        today_events   = today_events,
        later_events   = later_events,
        free_windows   = free_windows,
        focus_blocks   = focus_blocks,
        action_groups  = action_groups,
        radar          = radar,
        new_emails     = emails.get("new", []),
        lingering_emails = emails.get("lingering", []),
        improvement    = improvement,
    )
