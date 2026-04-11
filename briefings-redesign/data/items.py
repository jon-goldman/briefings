"""
Static definitions for action items and course schedule.
Update COURSES when syllabi change; add new items to ACTION_ITEMS.
"""
from datetime import date

# ---------------------------------------------------------------------------
# Action items — stable IDs map to briefing.js checkbox state
# ---------------------------------------------------------------------------

ACTION_ITEMS = [
    # Academic
    {"id": "heilbroner-fellowship",  "label": "Apply — Heilbroner Fellowship (deadline May 1)",          "group": "deadline"},
    {"id": "commentary-apr20",       "label": "Draft Commentary due Apr 20 (Politics of the Archive)",   "group": "deadline"},
    {"id": "commentary-may4",        "label": "Draft Commentary due May 4 (Politics of the Archive)",    "group": "deadline"},
    {"id": "prompt4-animating",      "label": "Prompt 4 — Animating Resistance",                         "group": "deadline"},
    # Inbox / digital
    {"id": "facebook-link",          "label": "Process saved Facebook link",                             "group": "errand"},
    {"id": "ikar-instagram",         "label": "Process saved IKAR Instagram post",                       "group": "errand"},
    {"id": "job-search-briefing",    "label": "Create job search briefing feature",                      "group": "errand"},
    {"id": "add-school-calendar",    "label": "Add school calendar to daily briefing",                   "group": "errand"},
    {"id": "notion-running-list",    "label": "Check Notion Running List",                               "group": "errand"},
    # People / comms
    {"id": "email-jamer",            "label": "Email Jamer",                                             "group": "errand"},
    {"id": "ezgi-letter",            "label": "Write Ezgi typewriter letter",                            "group": "errand"},
    # Money / admin
    {"id": "southwest-credits",      "label": "Southwest cancellation money / credits on Venture X",     "group": "errand"},
    {"id": "car-registration",       "label": "Registration in car",                                     "group": "errand"},
    # Physical errands
    {"id": "car-keys",               "label": "Get car keys from home",                                  "group": "errand"},
    {"id": "tea-lights",             "label": "Get tea lights (regular + larger)",                       "group": "errand"},
    {"id": "gold-chain",             "label": "Thin gold chain for Jewish star",                         "group": "errand"},
    {"id": "zip-tie",                "label": "Zip tie thingy",                                          "group": "errand"},
    {"id": "center-book-arts",       "label": "Go to Center for Book Arts",                              "group": "errand"},
    # Projects / fixes
    {"id": "fix-typewriter",         "label": "Fix typewriter",                                          "group": "errand"},
    {"id": "fix-whisker",            "label": "Fix whisker connection",                                  "group": "errand"},
    {"id": "analogy-note",           "label": "Write up seated/standing analogy note",                   "group": "errand"},
    {"id": "united-art-editions",    "label": "United Limited Art Editions 1957",                        "group": "errand"},
    {"id": "wardrobe-inventory",     "label": "Update wardrobe inventory",                               "group": "errand"},
    {"id": "clinton-hill-coop",      "label": "Look into Clinton Hill / Park Slope co-op",               "group": "errand"},
    {"id": "concert-briefing",       "label": "Create concert briefing feature",                         "group": "errand"},
    # Items that were previously one-off but may recur
    {"id": "dr-churchill-message",   "label": "Read therapist secure message",                           "group": "errand"},
    {"id": "iospa-billing",          "label": "Handle Dr. Iospa billing document",                       "group": "errand"},
]

# IDs that should never be permanently checked off (re-appear each run)
RECURRING_IDS = {"notion-running-list", "dr-churchill-message"}

# ---------------------------------------------------------------------------
# Course schedule — drives "On the Radar" and focus block suggestions
# ---------------------------------------------------------------------------

COURSES = [
    {
        "name": "Animating Resistance",
        "code": "NMDS 5446 A",
        "days": ["Thursday"],
        "time": "7:00–9:40pm",
        "location": "6 East 16th St., Room 611",
        "no_class": ["2026-04-23"],
        "readings": {
            "2026-04-16": [
                {"text": "Miner pp. 6–20", "minutes": 45},
            ],
            "2026-04-30": [
                {"text": "Galloway pp. 54–67", "minutes": 40},
            ],
            "2026-05-07": [
                {"text": "Stacey + Suchman pp. 1–46", "minutes": 150},
            ],
            "2026-05-14": [],  # Final presentations
        },
        "deadlines": [
            {"date": "2026-05-14", "label": "Final project presentations"},
            {"date": "2026-05-15", "label": "No-class makeup session"},
        ],
    },
    {
        "name": "Boundaries & Belonging",
        "code": "UTNS 6000",
        "days": ["Tuesday"],
        "time": "1:55–3:45pm",
        "location": "63 Fifth Ave, Room 304",
        "no_class": [],
        "readings": {
            "2026-04-14": [
                {"text": "Chircop, Efstathiou, Ticktin, Rogovoy (pages TBA)", "minutes": None},
            ],
            "2026-04-21": [
                {"text": "Media on the border (TBA)", "minutes": None},
            ],
            "2026-04-28": [
                {"text": "Stoetzer — Ruderal City (TBA)", "minutes": None},
            ],
            "2026-05-05": [
                {"text": "Benabdallah", "minutes": 30},
                {"text": "Brighi", "minutes": 60},
            ],
            "2026-05-12": [
                {"text": "Hughes — \"Leros: Island of Exile\" (TBA)", "minutes": None},
            ],
        },
        "deadlines": [
            {"date": "2026-05-21", "label": "Final due by 11:59pm"},
        ],
    },
    {
        "name": "Design Studio 2",
        "code": "PGTD 5101",
        "days": ["Monday", "Wednesday"],
        "time": "12:10–2:50pm",
        "location": "6 East 16th Ave, TD Studio",
        "no_class": [],
        "readings": {},
        "deadlines": [
            {"date": "2026-04-27", "label": "Assignment 3 presentation (Apr 27–29)"},
            {"date": "2026-05-04", "label": "Final — Wollman Hall"},
        ],
    },
    {
        "name": "Politics of the Archive",
        "code": "GHIS 5201",
        "days": ["Tuesday"],
        "time": "4:00–5:50pm",
        "location": "Room 1101, 6 E. 16th St.",
        "no_class": [],
        "readings": {
            "2026-04-14": [
                {"text": "Undocumented Migration Project site",  "minutes": 15},
                {"text": "Aviles",                               "minutes": 6},
                {"text": "Helton",                               "minutes": 60},
                {"text": "Giordano (TBA)",                       "minutes": None},
            ],
            "2026-04-21": [],
            "2026-04-28": [
                {"text": "Bubandt",   "minutes": 120},
                {"text": "Fahrmeir", "minutes": 50},
                {"text": "Schwartz", "minutes": 150},
            ],
            "2026-05-05": [
                {"text": "Harcourt",       "minutes": 45},
                {"text": "Ououha",         "minutes": 15},
                {"text": "Povinelli",      "minutes": 45},
                {"text": "Cifor",          "minutes": 60},
                {"text": "Cheikhali et al.", "minutes": 60},
            ],
            "2026-05-12": [
                {"text": "The Act of Killing (film, ~2h 39min)", "minutes": 159},
                {"text": "Juarez + Thomas (TBA)",                "minutes": None},
            ],
        },
        "deadlines": [
            {"date": "2026-04-20", "label": "Commentary due by 6pm (Mon)"},
            {"date": "2026-05-04", "label": "Commentary due by 6pm (Mon)"},
            {"date": "2026-05-15", "label": "Second essay (10pp) due"},
        ],
    },
    {
        "name": "Printmaking",
        "code": "",
        "days": ["Thursday"],
        "time": "Thursdays (studio)",
        "location": "Studio",
        "no_class": [],
        "readings": {},
        "deadlines": [
            {"date": "2026-05-07", "label": "Final project + critique"},
        ],
    },
]
