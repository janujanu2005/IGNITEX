from flask import Flask, render_template, request, send_file
import json, os
import pandas as pd
from datetime import datetime, timedelta
import google.generativeai as genai
import urllib.request
import urllib.error
from collections import Counter

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "your-gemini-api-key-here")
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-2.5-flash")

app = Flask(__name__)
UPLOAD_FOLDER = "uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# Absolute base directory — always the folder where app.py lives
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

os.makedirs(os.path.join(BASE_DIR, UPLOAD_FOLDER), exist_ok=True)
os.makedirs(os.path.join(BASE_DIR, "output"), exist_ok=True)


def parse_time_str(time_str):
    """Parse HH:MM or ISO 8601 time string into a naive datetime."""
    if not isinstance(time_str, str):
        time_str = str(time_str)
    time_str = time_str.strip()

    try:
        t = datetime.strptime(time_str, "%H:%M").time()
        dt = datetime.combine(datetime.now().date(), t)
        if dt > datetime.now():
            dt -= timedelta(days=1)
        return dt
    except Exception:
        pass

    try:
        return pd.to_datetime(time_str).to_pydatetime()
    except (ValueError, TypeError):
        pass

    return datetime.now()


def fetch_discord_messages(bot_token, channel_id):
    """Fetch last 100 messages from a Discord channel via Bot Token."""
    url = f"https://discord.com/api/v10/channels/{channel_id.strip()}/messages?limit=100"
    req = urllib.request.Request(url)
    req.add_header("Authorization", f"Bot {bot_token.strip()}")
    req.add_header("User-Agent", "DiscordBot (https://github.com/example, v2.0)")

    try:
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode("utf-8"))
            return [
                {
                    "user": m.get("author", {}).get("username", "Unknown"),
                    "message": m.get("content", ""),
                    "time": m.get("timestamp", ""),
                }
                for m in data
            ]
    except urllib.error.HTTPError as e:
        try:
            detail = json.loads(e.read().decode("utf-8")).get("message", e.reason)
        except Exception:
            detail = e.reason
        raise Exception(f"Discord API Error {e.code}: {detail}")
    except Exception as e:
        raise Exception(f"Failed to connect to Discord API: {str(e)}")


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/output/handover_note.md")
def download_handover():
    path = os.path.join(BASE_DIR, "handover_note.md")
    return send_file(path, as_attachment=True, download_name="handover_note.md")


@app.route("/docs/<filename>")
def download_doc(filename):
    allowed = {"README.md", "TEST_CASES.md", "EXPLANATION.md"}
    if filename not in allowed:
        from flask import abort
        abort(404)
    return send_file(os.path.join(BASE_DIR, filename),
                     as_attachment=True, download_name=filename)


@app.route("/test-data/<filename>")
def download_test_data(filename):
    allowed = {
        "tickets_test_full.csv", "discord_test_full.json",
        "smoke_tickets.csv", "smoke_discord.json",
        "tickets_duplicates.csv", "tickets_assignees.csv",
        "discord_empty.json",
    }
    if filename not in allowed:
        from flask import abort
        abort(404)
    return send_file(os.path.join(BASE_DIR, "test_data", filename),
                     as_attachment=True, download_name=filename)


@app.route("/generate", methods=["POST"])
def generate():
    discord_mode = request.form.get("discord_mode", "upload")
    ticket_file = request.files["tickets"]
    ticket_path = os.path.join(BASE_DIR, UPLOAD_FOLDER, ticket_file.filename)
    ticket_file.save(ticket_path)

    discord_data = []

    if discord_mode == "live":
        bot_token  = request.form.get("bot_token", "")
        channel_id = request.form.get("channel_id", "")
        if not bot_token or not channel_id:
            return render_template("index.html",
                                   error="Bot Token and Channel ID are required for Live Mode.")
        try:
            discord_data = fetch_discord_messages(bot_token, channel_id)
        except Exception as e:
            return render_template("index.html", error=str(e))
    else:
        discord_file = request.files.get("discord")
        if not discord_file or discord_file.filename == "":
            return render_template("index.html",
                                   error="Please upload a valid Discord export JSON file.")
        discord_path = os.path.join(BASE_DIR, UPLOAD_FOLDER, discord_file.filename)
        discord_file.save(discord_path)
        with open(discord_path, "r", encoding="utf-8") as f:
            discord_data = json.load(f)

    cutoff = datetime.now() - timedelta(hours=12)

    # Filter discord messages
    filtered = []
    for msg in discord_data:
        try:
            if parse_time_str(msg["time"]) >= cutoff:
                filtered.append(msg)
        except Exception:
            filtered.append(msg)
    discord_data = filtered

    # Filter ticket records
    tickets = pd.read_csv(ticket_path)
    if "created" in tickets.columns:
        tickets["created_parsed"] = tickets["created"].apply(parse_time_str)
        tickets = tickets[tickets["created_parsed"] >= cutoff]
        tickets = tickets.drop(columns=["created_parsed"])

    prompt = f"""
Review these messy chat logs and database tables. Identify overlapping issues where multiple messages or entries discuss the same underlying server problem. Merge them into a single descriptive tracking point so that nothing is repeated.

Discord Messages:
{discord_data}

Ticket Records:
{tickets.to_dict(orient='records')}

Cross-reference both sources.
Merge duplicate incidents.

Generate markdown sections using the exact headers below (include the numbering and spelling exactly):
### 1. High Priority Unresolved Fires
### 2. General System Fixes Delivered
### 3. Critical Infrastructure Monitor Watchlist
"""
    handover = model.generate_content(prompt).text

    handover_path = os.path.join(BASE_DIR, "handover_note.md")
    with open(handover_path, "w", encoding="utf-8") as f:
        f.write(handover)
    with open(os.path.join(BASE_DIR, "output", "handover_note.md"), "w", encoding="utf-8") as f:
        f.write(handover)

    # ── Chart data ────────────────────────────────────────
    priority_counts = {"Critical": 0, "High": 0, "Medium": 0, "Low": 0}
    if "priority" in tickets.columns:
        for p, c in tickets["priority"].value_counts().items():
            key = str(p).capitalize()
            if key in priority_counts:
                priority_counts[key] = int(c)

    status_counts = {}
    if "status" in tickets.columns:
        for s, c in tickets["status"].value_counts().items():
            status_counts[str(s)] = int(c)

    resolved_count   = status_counts.get("Resolved",   0)
    open_count       = status_counts.get("Open",       0)
    monitoring_count = status_counts.get("Monitoring", 0)

    # ── Duplicate detection ───────────────────────────────
    duplicates = []
    if "summary" in tickets.columns:
        seen = {}
        for _, row in tickets.iterrows():
            summary_words = frozenset(str(row.get("summary", "")).lower().split())
            for seen_words, seen_row in seen.items():
                overlap = summary_words & seen_words
                if len(overlap) >= 2:
                    duplicates.append({
                        "ticket_a":  str(row.get("ticket_id", "?")),
                        "ticket_b":  str(seen_row.get("ticket_id", "?")),
                        "summary_a": str(row.get("summary", "")),
                        "summary_b": str(seen_row.get("summary", "")),
                        "overlap":   " | ".join(sorted(overlap)),
                    })
            seen[summary_words] = row.to_dict()

    # ── Assignee recommendations ──────────────────────────
    ASSIGNEE_MAP = {
        "payment":  {"name": "Alice Johnson", "role": "Payments Engineer",   "avatar": "AJ"},
        "database": {"name": "Bob Martinez",  "role": "DBA / Infra Lead",    "avatar": "BM"},
        "cpu":      {"name": "Carol Singh",   "role": "SRE / DevOps",        "avatar": "CS"},
        "login":    {"name": "David Kim",     "role": "Auth Engineer",       "avatar": "DK"},
        "email":    {"name": "Eva Chen",      "role": "Notifications Team",  "avatar": "EC"},
        "server":   {"name": "Frank Osei",    "role": "Backend Engineer",    "avatar": "FO"},
        "network":  {"name": "Grace Liu",     "role": "Network Operations",  "avatar": "GL"},
        "default":  {"name": "On-Call SRE",   "role": "Shift Duty Engineer", "avatar": "OC"},
    }
    tickets_list = []
    if not tickets.empty:
        for _, row in tickets.iterrows():
            summary_lower = str(row.get("summary", "")).lower()
            assignee = ASSIGNEE_MAP["default"]
            for keyword, info in ASSIGNEE_MAP.items():
                if keyword != "default" and keyword in summary_lower:
                    assignee = info
                    break
            tickets_list.append({
                "ticket_id": str(row.get("ticket_id", "")),
                "status":    str(row.get("status",    "")),
                "priority":  str(row.get("priority",  "")),
                "summary":   str(row.get("summary",   "")),
                "created":   str(row.get("created",   "")),
                "assignee":  assignee,
            })

    return render_template(
        "result.html",
        handover=handover,
        timestamp=datetime.now().strftime("%d-%m-%Y %H:%M:%S"),
        discord_count=len(discord_data),
        ticket_count=len(tickets),
        total_records=len(discord_data) + len(tickets),
        priority_counts=json.dumps(priority_counts),
        status_counts=json.dumps(status_counts),
        resolved_count=resolved_count,
        open_count=open_count,
        monitoring_count=monitoring_count,
        duplicates=duplicates,
        tickets_list=tickets_list,
    )


if __name__ == "__main__":
    app.run(debug=True)
