# 🚀 Shift Handover Note Generator

> An AI-powered operational dashboard that aggregates Discord chat logs and ticket data, filters the last 12 hours, detects duplicates, recommends assignees, and generates a structured shift handover report using **Google Gemini AI**.

---

## 📸 Features

| Feature | Description |
|---|---|
| 🤖 **AI Deduplication** | Gemini AI cross-references Discord messages and CSV tickets to merge overlapping incidents |
| 📊 **Live Dashboard** | Interactive charts — donut, bar, horizontal bar, pie, and gauge — for incident metrics |
| 🔍 **Duplicate Detection** | Keyword-overlap algorithm flags tickets that describe the same incident |
| 👤 **Assignee Recommendations** | Keyword-based matching assigns each open ticket to a responsible engineer |
| ⏱️ **12-Hour Filter** | Only records created in the last 12 hours are processed |
| 📥 **Download Report** | Exports the AI-generated handover note as a `.md` file |
| 🎨 **Modern UI** | Colourful glassmorphism dark dashboard with animated charts and glowing components |

---

## 🗂️ Project Structure

```
ShiftHandOver/
│
├── app.py                    # Flask backend — all routes and logic
├── README.md                 # This file
├── tickets.csv               # Sample ticket data (for testing)
├── discord.json              # Sample Discord export (for testing)
├── handover_note.md          # Generated output (created after first run)
│
├── uploads/                  # Temp folder for uploaded files (auto-created)
├── output/                   # Backup copy of generated report (auto-created)
│
├── static/
│   └── css/
│       └── style.css         # Full dashboard stylesheet
│
└── templates/
    ├── index.html            # Upload / input page
    └── result.html           # Dashboard / results page
```

---

## ⚙️ Setup & Installation

### 1. Prerequisites

- Python 3.9 or higher
- pip

### 2. Install dependencies

```bash
pip install flask pandas google-generativeai
```

### 3. Run the app

```bash
cd C:\Users\<you>\Desktop\ShiftHandOver
python app.py
```

### 4. Open in browser

```
http://127.0.0.1:5000
```

---

## 🔑 Configuration

The Gemini API key is set directly in `app.py`:

```python
GEMINI_API_KEY = "your-key-here"
```

To get a free key: https://aistudio.google.com/app/apikey

---

## 🖥️ How to Use

### Option A — Upload JSON (recommended for testing)

1. Open `http://127.0.0.1:5000`
2. Click **Upload JSON** tab
3. Upload `discord.json` (sample provided in the project)
4. Upload `tickets.csv` (sample provided in the project)
5. Click **Generate Handover Note**

### Option B — Live Discord Channel

1. Create a Discord Bot at https://discord.com/developers/applications
2. Enable **Message Content Intent** under Bot settings
3. Add the bot to your server and copy the **Bot Token** and **Channel ID**
4. Paste them into the Live Channel form
5. Upload your `tickets.csv`
6. Click **Generate Handover Note**

---

## 📊 Dashboard Sections

After generating, the dashboard shows 6 sections navigable from the left sidebar:

| Section | What it shows |
|---|---|
| **Overview** | KPI cards (High/Critical, Open, Resolved, Duplicates, Total), risk banners, 3 mini charts |
| **Charts** | Full-size donut, bar, horizontal bar, and pie charts |
| **Tickets** | Searchable/filterable table with status pills, priority badges, assignee chips |
| **Duplicates** | Cards showing overlapping ticket pairs with shared keyword tags |
| **Assignees** | Cards matching each open ticket to a named engineer with role |
| **AI Report** | Full rendered Gemini markdown handover note |

---

## 🗃️ CSV Format

The tickets CSV must have these columns:

```
ticket_id, status, priority, summary, created
```

| Column | Values |
|---|---|
| `ticket_id` | Any unique number or string |
| `status` | `Open`, `Monitoring`, `Resolved` |
| `priority` | `Critical`, `High`, `Medium`, `Low` |
| `summary` | Free text description of the incident |
| `created` | Time in `HH:MM` format or ISO 8601 |

---

## 🗃️ Discord JSON Format

The Discord export JSON must be an array of message objects:

```json
[
  {
    "user": "username",
    "message": "message content",
    "time": "HH:MM"
  }
]
```

---

## 🔁 API Routes

| Route | Method | Description |
|---|---|---|
| `/` | GET | Renders the upload/input page |
| `/generate` | POST | Processes files and returns the dashboard |
| `/output/handover_note.md` | GET | Downloads the generated report file |

---

## 🧠 Assignee Keyword Map

| Keyword in summary | Assigned Engineer | Role |
|---|---|---|
| `payment` | Alice Johnson | Payments Engineer |
| `database` | Bob Martinez | DBA / Infra Lead |
| `cpu` | Carol Singh | SRE / DevOps |
| `login` | David Kim | Auth Engineer |
| `email` | Eva Chen | Notifications Team |
| `server` | Frank Osei | Backend Engineer |
| `network` | Grace Liu | Network Operations |
| *(default)* | On-Call SRE | Shift Duty Engineer |

---

## 🧪 Test Data Files

The project includes two ready-to-use test data files:

- **`tickets.csv`** — 5 sample tickets covering all priorities and statuses
- **`discord.json`** — 10 sample Discord messages covering various incidents

See `TEST_CASES.md` for detailed test scenarios.

---

## 📦 Dependencies

| Package | Purpose |
|---|---|
| `flask` | Web framework |
| `pandas` | CSV parsing and filtering |
| `google-generativeai` | Gemini AI API client |

All frontend libraries are loaded via CDN (no npm required):
- Chart.js 4.4.0
- Font Awesome 6.5.0
- marked.js (markdown rendering)
- Google Fonts — Inter, JetBrains Mono

---

## 🐛 Common Issues

| Error | Fix |
|---|---|
| `FileNotFoundError: handover_note.md` | Fixed — app now uses absolute paths. Restart Flask. |
| `ModuleNotFoundError` | Run `pip install flask pandas google-generativeai` |
| `Discord API Error 401` | Bot token is invalid or expired |
| `Discord API Error 403` | Bot lacks permission to read the channel |
| Port 5000 busy | Flask will print the actual port — open that URL instead |

---

## 👨‍💻 Tech Stack

- **Backend:** Python 3, Flask
- **AI:** Google Gemini 2.5 Flash
- **Frontend:** HTML5, CSS3 (custom), Vanilla JS
- **Charts:** Chart.js
- **Styling:** Inter font, glassmorphism dark theme

---

*Built for internal operations teams to automate shift-to-shift incident handovers.*
