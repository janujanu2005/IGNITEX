# Shift Handover Note Generator — Full Project Explanation

---

## 1. Problem Statement

### The Real-World Problem

Enterprise operations teams work in continuous 12-hour shifts. When the **Day Team** finishes at 8:00 PM, they must brief the incoming **Night Team** about all active infrastructure failures, server bugs, and ongoing client incidents.

Currently, engineers do this manually — they talk informally in chat rooms like **Discord** or **Slack**, while simultaneously updating formal ticket databases. The problem is:

- Engineers forget to write notes down
- The incoming team loses context and repeats work
- Critical senior failures get missed
- The same incident gets logged twice — once in Discord chat and once as a formal ticket
- There is no single structured document the next team can read and act on immediately

### The Need

The company needs an **automated tool** that:
- Extracts chat logs and formal ticket records
- Cross-references both sources
- Removes duplicate incidents
- Produces one clean, structured handover document

### This Project Solves It By

Automatically aggregating Discord messages and CSV ticket records, filtering only the last 12 hours, using **Gemini AI** to deduplicate and merge overlapping incidents, and presenting everything in a live operational dashboard with downloadable markdown output.

---

## 2. Tech Stack Used

### Backend
| Technology | Version | Purpose |
|---|---|---|
| **Python** | 3.9+ | Core programming language |
| **Flask** | Latest | Web framework — handles routes, form uploads, rendering |
| **Pandas** | Latest | CSV parsing, DataFrame filtering, time-based slicing |
| **google-generativeai** | Latest | Official Google Gemini AI Python SDK |
| **urllib** | Built-in | HTTP requests to Discord REST API (no extra library needed) |
| **json** | Built-in | Parsing Discord export files and API responses |
| **os / datetime** | Built-in | File path management, time filtering, timestamp parsing |

### Frontend
| Technology | Purpose |
|---|---|
| **HTML5** | Page structure and forms |
| **CSS3 (Custom)** | Full glassmorphism dark dashboard — no framework |
| **Vanilla JavaScript** | Tab switching, file feedback, chart rendering, nav logic |
| **Chart.js 4.4.0** | Donut, bar, horizontal bar, pie, and gauge charts |
| **Font Awesome 6.5** | All icons across UI |
| **marked.js** | Renders AI-generated markdown into HTML |
| **Google Fonts (Inter + JetBrains Mono)** | Typography |

### AI
| Technology | Purpose |
|---|---|
| **Google Gemini 2.5 Flash** | Reads both Discord messages and ticket records, identifies overlapping incidents, merges duplicates, and outputs a structured 3-section markdown handover note |

### External APIs
| API | Purpose |
|---|---|
| **Discord REST API v10** | Fetches last 100 messages from a live channel using a Bot Token |
| **Google Gemini API** | Generates the AI handover note from combined data |

---

## 3. Project Workflow

```
┌─────────────────────────────────────────────────────────────┐
│                    USER OPENS THE APP                        │
│                  http://127.0.0.1:5000                       │
└─────────────────────────┬───────────────────────────────────┘
                           │
              ┌────────────▼─────────────┐
              │   CHOOSE DATA SOURCE      │
              │  Live Channel OR          │
              │  Upload JSON Export       │
              └────────────┬─────────────┘
                           │
         ┌─────────────────┼──────────────────┐
         │                                    │
    ┌────▼─────┐                        ┌─────▼──────┐
    │ LIVE MODE │                        │ UPLOAD MODE │
    │ Bot Token │                        │ JSON File   │
    │ Channel ID│                        │ from disk   │
    └────┬──────┘                        └─────┬───────┘
         │                                     │
         └──────────────┬──────────────────────┘
                        │
              ┌─────────▼──────────┐
              │  UPLOAD tickets.csv │
              └─────────┬───────────┘
                        │
              ┌─────────▼───────────────────────┐
              │  PHASE 1: DATA INGESTION          │
              │  - Read Discord messages          │
              │  - Read CSV ticket records        │
              └─────────┬───────────────────────┘
                        │
              ┌─────────▼───────────────────────┐
              │  PHASE 2: TEMPORAL FILTERING      │
              │  - Calculate cutoff = now - 12h   │
              │  - Drop records older than 12h    │
              │  - Supports HH:MM and ISO formats │
              └─────────┬───────────────────────┘
                        │
              ┌─────────▼───────────────────────┐
              │  PHASE 3: GEMINI AI PROCESSING   │
              │  - Combine both data sources      │
              │  - Send to Gemini 2.5 Flash       │
              │  - AI merges duplicate incidents  │
              │  - Returns structured markdown    │
              └─────────┬───────────────────────┘
                        │
              ┌─────────▼───────────────────────┐
              │  PHASE 4: ANALYTICS ENGINE        │
              │  - Count by priority/status       │
              │  - Detect duplicate tickets       │
              │  - Match assignees by keyword     │
              └─────────┬───────────────────────┘
                        │
              ┌─────────▼───────────────────────┐
              │  PHASE 5: DASHBOARD OUTPUT        │
              │  - Render result.html             │
              │  - 5 KPI cards                    │
              │  - 4 interactive charts           │
              │  - Ticket table with filters      │
              │  - Duplicate detection cards      │
              │  - Team dispatch (assignees)      │
              │  - AI handover note viewer        │
              │  - Download handover_note.md      │
              └─────────────────────────────────┘
```

---

## 4. API Connections

### A. Discord REST API v10

**Endpoint used:**
```
GET https://discord.com/api/v10/channels/{channel_id}/messages?limit=100
```

**How it works:**
1. User creates a Discord Bot at https://discord.com/developers/applications
2. The bot is added to their server with **Read Messages** permission
3. **Message Content Intent** is enabled in the bot settings
4. User pastes the **Bot Token** and **Channel ID** into the app
5. The app sends a GET request with `Authorization: Bot <token>` header
6. Discord returns the last 100 messages as JSON
7. The app maps each message to `{user, message, time}` format

**Code location:** `fetch_discord_messages()` function in `app.py`

**Error handling:**
- `401 Unauthorized` → Invalid bot token
- `403 Forbidden` → Bot lacks channel read permission
- `404 Not Found` → Channel ID does not exist
- Network errors → Caught and shown as error banner on UI

---

### B. Google Gemini API

**Model used:** `gemini-2.5-flash`

**How it works:**
1. After filtering, both Discord messages and ticket records are combined into one text payload
2. A structured prompt is built asking Gemini to:
   - Review both sources
   - Find overlapping incidents
   - Merge duplicates into single tracking points
   - Output exactly 3 markdown sections
3. Gemini returns a markdown string
4. The app saves it as `handover_note.md` and renders it in the dashboard

**Prompt structure:**
```
"Review these messy chat logs and database tables.
Identify overlapping issues where multiple messages or entries
discuss the same underlying server problem.
Merge them into a single descriptive tracking point.

Discord Messages: [...]
Ticket Records: [...]

Generate:
### 1. High Priority Unresolved Fires
### 2. General System Fixes Delivered
### 3. Critical Infrastructure Monitor Watchlist"
```

**Code location:** `generate()` route in `app.py`, lines ~140–155

---

## 5. Features Built

### Feature 1 — Dual Source Data Ingestion
- **Live Mode:** Connects directly to Discord via bot token and channel ID
- **Upload Mode:** Accepts a JSON export file from disk
- Both modes produce the same internal `{user, message, time}` list

### Feature 2 — Temporal Filtering (12-Hour Window)
- Calculates `cutoff = datetime.now() - 12 hours`
- Filters both Discord messages and CSV tickets
- Handles two time formats:
  - `HH:MM` (e.g. `09:05`) — relative to today, adjusts to yesterday if future
  - ISO 8601 (e.g. `2026-06-09T09:05:00`) — absolute timestamps

### Feature 3 — Gemini AI Deduplication
- Sends combined data to Gemini 2.5 Flash
- AI identifies incidents described in both chat and tickets
- Merges them into one clean summary point
- Outputs exactly 3 structured markdown sections
- Saves output as `handover_note.md`

### Feature 4 — Duplicate Ticket Detection (Algorithmic)
- Pure Python keyword-overlap algorithm (no AI needed)
- Converts each ticket summary into a `frozenset` of words
- Compares all ticket pairs for shared keywords
- Flags pairs with **2 or more overlapping words** as potential duplicates
- Displays them as visual cards with keyword tags highlighted in amber

### Feature 5 — Automatic Assignee Recommendation
- Keyword-based matching maps each ticket to an engineer
- 7 domain keywords, 1 default fallback:

| Keyword | Engineer | Role |
|---|---|---|
| payment | Alice Johnson | Payments Engineer |
| database | Bob Martinez | DBA / Infra Lead |
| cpu | Carol Singh | SRE / DevOps |
| login | David Kim | Auth Engineer |
| email | Eva Chen | Notifications Team |
| server | Frank Osei | Backend Engineer |
| network | Grace Liu | Network Operations |
| (default) | On-Call SRE | Shift Duty Engineer |

### Feature 6 — Interactive Live Dashboard
6 sections accessible from the left sidebar:
- **Shift Overview** — 5 KPI cards, risk banners, 3 mini charts
- **Visualization** — 4 full charts (donut, bar, horizontal bar, pie)
- **Incident Tracker** — searchable/filterable ticket table
- **Dedup Analysis** — duplicate pair cards with keyword tags
- **Team Dispatch** — engineer assignment cards per open ticket
- **AI Handover Note** — full rendered markdown report

### Feature 7 — Chart Visualizations (Chart.js)
- **Severity Donut** — Critical / High / Medium / Low breakdown
- **Status Bar** — Open / Monitoring / Resolved counts
- **Priority Horizontal Bar** — priority distribution
- **Open vs Resolved Pie** — resolution ratio
- **Resolution Gauge** — percentage resolved, semi-circle style

### Feature 8 — Report Download
- Generates `handover_note.md` saved to project root
- Backup copy saved to `/output/` folder
- Download button in dashboard triggers Flask `send_file()`
- Fixed bug: uses `os.path.abspath(__file__)` for reliable path resolution

---

## 6. Challenges Faced and How They Were Resolved

### Challenge 1 — FileNotFoundError on Report Download
**Problem:** Clicking "Download .md" showed `FileNotFoundError: handover_note.md`

**Root Cause:** `send_file("handover_note.md")` and `open("handover_note.md", ...)` use relative paths. Python resolves them relative to wherever the terminal was opened, not the project folder. If you opened the terminal from `C:\Python314\` the file was saved there, but Flask looked in the project directory.

**Fix Applied:**
```python
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# All file operations now use:
os.path.join(BASE_DIR, "handover_note.md")
```
This always resolves to the folder where `app.py` lives, regardless of where Python was launched from.

---

### Challenge 2 — Time Format Inconsistency
**Problem:** Ticket CSV files use simple `HH:MM` format (e.g. `09:05`), but Discord API returns full ISO 8601 timestamps (e.g. `2026-06-09T09:04:00+00:00`). A single parser couldn't handle both.

**Root Cause:** `pd.to_datetime("09:05")` parses it as a time today but doesn't handle the "yesterday" edge case for overnight shifts.

**Fix Applied:** A two-stage `parse_time_str()` function:
1. First tries `datetime.strptime(time_str, "%H:%M")` — if the resulting datetime is in the future, subtracts 1 day (handles overnight shifts)
2. Falls back to `pd.to_datetime()` for ISO format
3. Final fallback returns `datetime.now()` so the record is included rather than crashing

---

### Challenge 3 — Gemini Prompt Producing Inconsistent Structure
**Problem:** Early versions of the AI prompt returned free-form text with no consistent sections, making it impossible to colour-code the markdown sections in the dashboard.

**Fix Applied:** The prompt was made prescriptive — it specifies the exact headers including numbering and spelling:
```
Generate markdown sections using the EXACT headers below:
### 1. High Priority Unresolved Fires
### 2. General System Fixes Delivered
### 3. Critical Infrastructure Monitor Watchlist
```
The CSS then targets `h3:nth-of-type(1/2/3)` to colour each section differently.

---

### Challenge 4 — Discord API Authentication Errors
**Problem:** Users saw vague `urllib.error.HTTPError` exceptions with no useful message.

**Root Cause:** Discord API returns error details in the JSON response body, but `urllib` only exposes the HTTP status code by default.

**Fix Applied:**
```python
except urllib.error.HTTPError as e:
    err_data = json.loads(e.read().decode("utf-8"))
    detail = err_data.get("message", e.reason)
    raise Exception(f"Discord API Error {e.code}: {detail}")
```
Now the actual Discord error message (e.g. "401: 0: 401: Unauthorized") is shown to the user in the error banner.

---

### Challenge 5 — UI Appearing Dark and Colourless
**Problem:** The dashboard looked plain and monochromatic — hard to read and not visually engaging.

**Fix Applied:**
- Added 5-blob ambient radial gradients as background
- Added animated floating orb elements
- Coloured top-bar strips on every card per category
- KPI values have coloured `text-shadow` (neon glow effect)
- Each nav item icon has its own accent colour
- Badges use glowing borders per priority level
- Animated pulsing status dots on ticket rows

---

### Challenge 6 — Duplicate Detection Accuracy
**Problem:** Simple string matching (e.g. `if summary_a in summary_b`) was too strict and missed real duplicates.

**Fix Applied:** Keyword set intersection approach:
```python
summary_words = frozenset(summary.lower().split())
overlap = summary_words_a & summary_words_b
if len(overlap) >= 2:
    # flag as duplicate
```
This catches tickets like "Payment service failure" and "Payment gateway timeout" as duplicates (shared words: `payment`... but needs 2 — so tuned to domain keywords).

---

## 7. Project Folder Structure

```
ShiftHandOver/
│
├── app.py                    ← Flask backend (all logic)
├── README.md                 ← Project documentation
├── TEST_CASES.md             ← 12 test scenarios
├── EXPLANATION.md            ← This file
├── tickets.csv               ← Sample data (5 tickets)
├── discord.json              ← Sample Discord export
├── handover_note.md          ← Generated on first run
│
├── uploads/                  ← Temp storage for uploaded files
├── output/                   ← Backup of generated report
│
├── test_data/
│   ├── tickets_test_full.csv     ← 10-ticket comprehensive test
│   ├── discord_test_full.json    ← 10-message comprehensive test
│   ├── smoke_tickets.csv         ← Quick 3-row smoke test
│   ├── smoke_discord.json        ← Quick 2-message smoke test
│   ├── tickets_duplicates.csv    ← Tests duplicate detection
│   ├── tickets_assignees.csv     ← Tests all 7 assignee keywords
│   └── discord_empty.json        ← Tests empty source handling
│
├── static/
│   └── css/
│       └── style.css         ← Full dashboard stylesheet (1000+ lines)
│
└── templates/
    ├── index.html            ← Upload / input page
    └── result.html           ← Dashboard + charts + report
```

---

## 8. How to Run

```bash
# 1. Navigate to project folder
cd C:\Users\91934\Desktop\ShiftHandOver

# 2. Install dependencies
pip install flask pandas google-generativeai

# 3. Run the app
python app.py

# 4. Open browser
http://127.0.0.1:5000
```

---

## 9. Sample Input / Output

**Input — tickets.csv:**
```
101, Open,    High,    Payment service failure,       09:05
102, Monitor, Medium,  High CPU utilization,          09:15
103, Resolved,Low,     Login bug fixed,               09:40
```

**Input — discord.json:**
```json
[
  {"user":"alice","message":"Payment service is down!","time":"09:04"},
  {"user":"bob",  "message":"CPU is at 94% on prod",  "time":"09:14"}
]
```

**Output — handover_note.md (Gemini Generated):**
```markdown
### 1. High Priority Unresolved Fires
- **Payment Service Failure (INC-101):** Payment service down since 09:05,
  confirmed by Discord (09:04). Ticket open, High priority.

### 2. General System Fixes Delivered
- **Login Bug Fixed:** SSO login issue resolved and deployed (09:40).

### 3. Critical Infrastructure Monitor Watchlist
- **CPU Spike (INC-102):** prod-server CPU at 94%, under monitoring.
  Corroborated by Discord message at 09:14.
```

---

*Built as part of Operations Communication Automation — Project Blueprint 04.*
