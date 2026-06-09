# 🧪 Test Cases — Shift Handover Note Generator

This document covers all test scenarios, expected outcomes, and the sample test data files to use.

---

## 📁 Test Data Files

### `tickets.csv` — Extended Test Dataset

Copy this content into a file named `tickets_test_full.csv` for comprehensive testing:

```csv
ticket_id,status,priority,summary,created
101,Open,High,Payment service failure causing checkout errors,09:05
102,Monitoring,Medium,High CPU utilization on prod-server-3,09:15
103,Resolved,Low,Login bug fixed for SSO users,09:40
104,Open,Medium,Email notification delay over 30 minutes,10:15
105,Resolved,High,Database connection issue fixed on replica,23:00
106,Open,Critical,Payment gateway timeout affecting all transactions,10:30
107,Open,High,Network latency spike on eu-west cluster,11:00
108,Monitoring,Medium,Server memory usage above 85 percent threshold,11:20
109,Resolved,Low,Email template rendering bug resolved,08:30
110,Open,Critical,Database primary node unresponsive,11:45
```

---

### `discord.json` — Extended Test Dataset

Copy this content into a file named `discord_test_full.json`:

```json
[
  {
    "user": "ops_alice",
    "message": "Payment service is down, checkout is failing for all users. Raised ticket 101.",
    "time": "09:04"
  },
  {
    "user": "sre_bob",
    "message": "Confirmed - payment gateway is timing out. Looking into it now.",
    "time": "09:06"
  },
  {
    "user": "ops_carol",
    "message": "prod-server-3 CPU is at 94%, opened monitoring ticket.",
    "time": "09:14"
  },
  {
    "user": "dev_david",
    "message": "SSO login bug has been patched and deployed to prod.",
    "time": "09:38"
  },
  {
    "user": "ops_alice",
    "message": "Email notifications are queuing up, delay is 35+ minutes. Users are complaining.",
    "time": "10:13"
  },
  {
    "user": "sre_bob",
    "message": "Database replica connection issue is fixed. Primary is stable.",
    "time": "10:50"
  },
  {
    "user": "ops_carol",
    "message": "Payment gateway still throwing 504s. This looks like ticket 101 and 106 are the same issue.",
    "time": "10:31"
  },
  {
    "user": "infra_grace",
    "message": "Network team sees latency spike on eu-west. Investigating BGP route change.",
    "time": "11:02"
  },
  {
    "user": "sre_frank",
    "message": "Server memory alert on prod-server-3 and prod-server-5. Could be related to the CPU spike.",
    "time": "11:22"
  },
  {
    "user": "dba_bob",
    "message": "CRITICAL: database primary node is not responding. Failover initiated.",
    "time": "11:44"
  }
]
```

---

## ✅ Test Case 1 — Happy Path (Upload Mode)

**Scenario:** Normal run with valid CSV and Discord JSON upload.

**Steps:**
1. Start Flask: `python app.py`
2. Open `http://127.0.0.1:5000`
3. Select **Upload JSON** tab
4. Upload `discord_test_full.json`
5. Upload `tickets_test_full.csv`
6. Click **Generate Handover Note**

**Expected Results:**
- ✅ Dashboard loads with Overview section active
- ✅ KPI cards show correct counts (Open: 5, Resolved: 3, Monitoring: 2)
- ✅ High/Critical KPI shows 4
- ✅ 3 mini charts visible (donut, bar, gauge)
- ✅ Risk banners appear for tickets 101, 106, 107, 110 (High/Critical + Open)
- ✅ AI report rendered with 3 markdown sections

---

## ✅ Test Case 2 — Duplicate Detection

**Scenario:** Two tickets describe the same payment issue.

**Tickets to use:**
```csv
ticket_id,status,priority,summary,created
101,Open,High,Payment service failure causing checkout errors,09:05
106,Open,Critical,Payment gateway timeout affecting all transactions,10:30
```

**Expected Results:**
- ✅ Duplicates section shows at least 1 duplicate card
- ✅ Tickets 101 and 106 flagged (share keywords: `payment`, `service`/`gateway`)
- ✅ Duplicate badge appears on nav sidebar
- ✅ Shared keywords displayed as amber pills

---

## ✅ Test Case 3 — Assignee Recommendations

**Scenario:** Each ticket should map to the correct engineer.

**Tickets to use:**
```csv
ticket_id,status,priority,summary,created
201,Open,High,Payment service failure,09:05
202,Open,Medium,High CPU utilization on server,09:15
203,Open,High,Database connection issue on replica,09:40
204,Open,Medium,Email notification delay,10:15
205,Open,High,Login page returning 500 error,10:30
206,Open,Medium,Network packet loss detected,11:00
207,Open,Low,Server disk usage at 90 percent,11:20
```

**Expected Assignees:**

| Ticket | Keyword | Assigned To |
|---|---|---|
| 201 | `payment` | Alice Johnson — Payments Engineer |
| 202 | `cpu` | Carol Singh — SRE / DevOps |
| 203 | `database` | Bob Martinez — DBA / Infra Lead |
| 204 | `email` | Eva Chen — Notifications Team |
| 205 | `login` | David Kim — Auth Engineer |
| 206 | `network` | Grace Liu — Network Operations |
| 207 | `server` | Frank Osei — Backend Engineer |

---

## ✅ Test Case 4 — Chart Data Accuracy

**Scenario:** Verify all chart values match the input data.

**Tickets to use:**
```csv
ticket_id,status,priority,summary,created
301,Open,Critical,Critical database failure,09:00
302,Open,High,High CPU usage,09:10
303,Monitoring,Medium,Medium network latency,09:20
304,Resolved,Low,Low disk usage alert resolved,09:30
305,Resolved,High,High memory alert resolved,09:40
```

**Expected Chart Values:**

| Chart | Expected |
|---|---|
| Severity Donut | Critical: 1, High: 2, Medium: 1, Low: 1 |
| Status Bar | Open: 2, Monitoring: 1, Resolved: 2 |
| Priority H-Bar | Critical: 1, High: 2, Medium: 1, Low: 1 |
| Open vs Resolved Pie | Open: 2, Resolved: 2, Monitoring: 1 |
| Resolution Gauge | 40% (2 out of 5 resolved) |

---

## ✅ Test Case 5 — 12-Hour Filter

**Scenario:** Only tickets within the last 12 hours should appear.

**Setup:** Set two tickets with old times (will be filtered out) and two with recent times.

```csv
ticket_id,status,priority,summary,created
401,Open,High,Recent payment issue,09:00
402,Resolved,Medium,Recent login fix,10:00
```

> **Note:** Since the app uses `HH:MM` format relative to today, both tickets above will always be within 12 hours if you run the test during the same day. Use ISO timestamps to test filtering explicitly:

```csv
ticket_id,status,priority,summary,created
501,Open,High,Recent payment issue,2026-06-09T10:00:00
502,Open,Medium,Old network issue,2026-01-01T10:00:00
```

**Expected Results:**
- ✅ Only ticket 501 appears (ticket 502 is older than 12 hours)
- ✅ Total records count = 1 ticket

---

## ✅ Test Case 6 — Download Report

**Scenario:** Verify the handover note downloads correctly.

**Steps:**
1. Complete any successful generation (Test Case 1)
2. Click **Download .md** button in the dashboard hero bar

**Expected Results:**
- ✅ Browser downloads `handover_note.md`
- ✅ File contains the 3 markdown sections
- ✅ No `FileNotFoundError`

---

## ✅ Test Case 7 — Empty Discord, Valid CSV

**Scenario:** Discord JSON is an empty array.

**discord_empty.json:**
```json
[]
```

**tickets.csv:** Use the standard 5-row sample.

**Expected Results:**
- ✅ App processes successfully (no crash)
- ✅ Discord count shows 0
- ✅ Charts show ticket data only
- ✅ AI report generated from tickets alone

---

## ✅ Test Case 8 — Tickets Filtered to Zero

**Scenario:** All tickets are older than 12 hours.

```csv
ticket_id,status,priority,summary,created
601,Open,High,Old payment issue,2025-01-01T09:00:00
602,Resolved,Low,Old server fix,2025-01-01T10:00:00
```

**Expected Results:**
- ✅ App handles empty ticket DataFrame gracefully
- ✅ All KPI values show 0
- ✅ Charts render with no data (empty state)
- ✅ AI report generates with only Discord messages

---

## ✅ Test Case 9 — Missing Tickets File

**Scenario:** User submits form without uploading tickets CSV.

**Steps:**
1. Open the form
2. Do NOT attach any CSV file
3. Click Generate

**Expected Results:**
- ✅ Browser blocks submission (HTML5 `required` attribute on file input)
- ✅ Error shown: "Please fill out this field"
- ✅ No Flask error

---

## ✅ Test Case 10 — Invalid Discord JSON

**Scenario:** Upload a malformed JSON file.

**bad_discord.json:**
```json
{ "this": "is not an array" }
```

**Expected Results:**
- ✅ App returns error page / error banner
- ✅ No unhandled server crash (500 error)

---

## ✅ Test Case 11 — All Statuses Present

**Scenario:** Verify all three status types render correctly in the table.

```csv
ticket_id,status,priority,summary,created
701,Open,High,Payment failure,09:00
702,Monitoring,Medium,CPU spike monitoring,09:30
703,Resolved,Low,Email issue resolved,10:00
```

**Expected Results:**
- ✅ Open row shows pulsing indigo dot
- ✅ Monitoring row shows pulsing amber dot  
- ✅ Resolved row shows static green dot
- ✅ Status filter dropdown correctly shows/hides each row

---

## ✅ Test Case 12 — Table Search & Filter

**Scenario:** Verify search and filter controls work.

**Steps (after generating with multi-row CSV):**
1. Go to **Tickets** section
2. Type `payment` in the search box → only payment tickets visible
3. Select `Open` in Status filter → only open tickets visible
4. Select `High` in Priority filter → only high priority visible
5. Clear all filters → all rows return

**Expected Results:**
- ✅ Each filter works independently
- ✅ Filters stack (all three can be active together)
- ✅ Rows hide/show instantly without page reload

---

## 📋 Minimum Viable Test (Quick Smoke Test)

Use these two files for a fast end-to-end check:

**`smoke_tickets.csv`:**
```csv
ticket_id,status,priority,summary,created
1,Open,High,Payment gateway down,09:00
2,Resolved,Medium,CPU spike fixed,10:00
3,Monitoring,Low,Email queue delay,11:00
```

**`smoke_discord.json`:**
```json
[
  {"user": "alice", "message": "Payment service is broken!", "time": "09:01"},
  {"user": "bob",   "message": "CPU usage is back to normal.", "time": "10:05"}
]
```

**Expected:** Dashboard loads, 2 discord messages, 3 tickets, AI report with 3 sections, download works.
