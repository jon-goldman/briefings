# Daily Briefing — Claude Code Instructions

This project generates a daily HTML briefing for Jon (jongoldman93@gmail.com),
publishes it to GitHub Pages, and creates a Gmail draft summary.

---

## Run the briefing

```bash
python briefing.py
```

That's it. The script handles everything: memory load, parallel data fetch,
HTML render, GitHub push, Gmail draft.

### Options

```bash
python briefing.py --dry-run          # Render to /tmp only — no push, no draft
python briefing.py --skip-draft       # Push to Pages but skip Gmail draft
python briefing.py --date 2026-04-12  # Generate for a specific date
```

---

## Environment

All secrets live in `.env` (gitignored). Required variables:

| Variable | Purpose |
|---|---|
| `GOOGLE_CLIENT_ID` | Google OAuth client ID |
| `GOOGLE_CLIENT_SECRET` | Google OAuth client secret |
| `GOOGLE_REFRESH_TOKEN` | Long-lived refresh token (run `setup_auth.py` once) |
| `NOTION_API_KEY` | Notion integration token |
| `GITHUB_PAT` | GitHub PAT with `repo` scope |

---

## First-time setup

```bash
pip install -r requirements.txt
cp .env.example .env
# Edit .env with NOTION_API_KEY and GITHUB_PAT (you already have these)
python setup_auth.py   # Opens browser for Google OAuth; prints tokens to paste into .env
python briefing.py --dry-run   # Verify render is correct
python briefing.py             # Full run
```

---

## Project structure

```
briefing.py          Entry point — async orchestrator
render.py            Builds HTML from data; contains all grouping/focus logic
push.py              GitHub Contents API — pushes HTML + updates index.html
draft.py             Creates compact Gmail draft

sources/
  auth.py            Google OAuth credential refresh
  weather.py         wttr.in JSON — no auth required
  memory.py          GitHub-backed memory.json read/write
  gmail.py           Gmail API — new + lingering inbox threads
  calendar_source.py Google Calendar API + free-window computation
  notion.py          Notion REST API — running list page

data/
  items.py           ACTION_ITEMS list + COURSES schedule (update when syllabi change)

template.html        Jinja2 HTML template
```

---

## Updating course data

When a syllabus changes, edit `data/items.py`:
- `COURSES` — class days, reading assignments, deadlines
- `ACTION_ITEMS` — persistent to-do items (add new ones here, never delete old ones)
- `RECURRING_IDS` — items that should re-appear even after being checked

---

## Scheduling (Claude Code hook)

To run automatically every morning, add this to `.claude/settings.json`:

```json
{
  "hooks": {
    "morning-briefing": {
      "schedule": "0 7 * * 1-5",
      "command": "cd /path/to/briefings && python briefing.py"
    }
  }
}
```

Or use the Cowork schedule MCP to trigger it via the scheduled-tasks tool.

---

## Debugging

- **Dry run**: `python briefing.py --dry-run` renders to `/tmp/daily-briefing-YYYY-MM-DD.html`
- **Individual sources**: Each `sources/*.py` module can be run standalone with `python -c "import asyncio; from sources.weather import get_weather; print(asyncio.run(get_weather()))"`
- **Memory inspection**: `cat memory.json` or visit https://github.com/jon-goldman/briefings/blob/main/memory.json
- **Logs**: Warnings print to stderr; the script never exits on partial failures

---

## Key design decisions

1. **All data fetched in parallel** via `asyncio.gather()` — total wall time ~3–5s vs 20s+ sequential
2. **Graceful degradation** — any source failure produces a warning and a fallback; briefing still publishes
3. **Idempotent push** — compares content hash before pushing; no duplicate GitHub commits on re-runs
4. **Memory lives in GitHub** — no database, no local state; survives machine wipes and is human-readable
5. **Google API is sync** — runs in `asyncio`'s thread executor; doesn't block the event loop
6. **Jinja2 template** — HTML structure is separate from render logic; edit `template.html` to change layout
