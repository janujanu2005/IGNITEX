# AI Usage Note
**Project:** Shift Handover Note Generator
**Student:** Nagendiran P
**Date:** June 2026

---

## What AI Helped With

### 1. Code Generation
- Generated the core Flask route structure for `/generate`, `/output/handover_note.md`, and file download endpoints
- Wrote the `parse_time_str()` function to handle both `HH:MM` and ISO 8601 time formats with overnight shift logic
- Built the duplicate detection algorithm using `frozenset` keyword intersection
- Generated the keyword-based assignee matching logic with 7 domain engineers and a fallback
- Created all Chart.js chart functions — donut, bar, horizontal bar, pie, and gauge

### 2. UI / Frontend
- Designed the full glassmorphism dark dashboard layout with CSS variables and gradient tokens
- Created animated background orbs, dot-grid overlay, and rainbow navbar strip
- Built the 6-section sidebar navigation with coloured icons and active state indicators
- Designed KPI cards with glowing top bars, neon text shadows, and hover lift effects
- Created the colourful index page with animated title gradient, floating orbs, and feature tags

### 3. Debugging
- Fixed `FileNotFoundError` on report download by switching to `os.path.abspath(__file__)` for absolute path resolution
- Fixed GitHub Push Protection block by moving API key from hardcoded string to `os.environ.get()`
- Fixed `git push` rejected error by running `git pull --allow-unrelated-histories` first
- Fixed Pytest import error caused by missing `app.py` after Git merge

### 4. Test Suite
- Generated all 43 Pytest test cases across 7 test classes
- Wrote `monkeypatch` mock for Gemini API so happy path tests run without real API calls
- Structured tests using pytest fixtures (`client`, `sample_tickets_csv`, `empty_discord_json`)

### 5. Documentation
- Wrote README.md with setup instructions, CSV format, route table, and assignee map
- Wrote TEST_CASES.md with 12 detailed test scenarios and expected results
- Wrote EXPLANATION.md with full problem statement, tech stack, workflow diagram, API connection details, challenges, and solutions

---

## What AI Got Wrong

### 1. File Path Bug
- AI initially used `send_file("handover_note.md")` with a relative path
- This caused `FileNotFoundError` because it resolved to the terminal's working directory, not the project folder
- Had to manually debug and fix by adding `BASE_DIR = os.path.dirname(os.path.abspath(__file__))`

### 2. Hardcoded API Key
- AI placed the Gemini API key directly in `app.py` as a string
- GitHub's Push Protection detected it and blocked the push with `GH013: Repository rule violations`
- Had to rewrite as `os.environ.get("GEMINI_API_KEY", "placeholder")`

### 3. Git Commands for Wrong Shell
- AI suggested `/c/Users/...` path syntax (Git Bash format) when I was using CMD/PowerShell
- CMD gave error: `Cannot find path 'C:\c\Users\...'`
- Had to switch between shells and re-run commands

### 4. Pytest Test — Empty Discord Not Mocked
- One test (`test_upload_with_empty_discord_json`) was written without mocking Gemini
- It tried to call the real Gemini API with an invalid placeholder key
- Got `400 API key not valid` error — 1 test failed
- Fixed by adding `monkeypatch` mock to that test as well

### 5. Git History Issue
- AI's `git commit --amend` suggestion didn't fully rewrite the history
- Old commit `56fccbf7` still contained the API key
- GitHub still blocked because the key was in commit history, not just the current file
- Had to use `git push --force` after fixing the file

---

## Best Prompts Used

### Prompt 1 — AI Deduplication (Core Feature)
```
Review these messy chat logs and database tables.
Identify overlapping issues where multiple messages or entries
discuss the same underlying server problem.
Merge them into a single descriptive tracking point so nothing is repeated.

Discord Messages: [...]
Ticket Records: [...]

Cross-reference both sources. Merge duplicate incidents.

Generate markdown sections using the EXACT headers below:
### 1. High Priority Unresolved Fires
### 2. General System Fixes Delivered
### 3. Critical Infrastructure Monitor Watchlist
```
**Why it worked:** Specifying exact headers with numbering forced Gemini to produce consistent, parseable output every time. Without this, the sections were random and CSS colour-coding broke.

---

### Prompt 2 — Dashboard UI Design
```
Build a glassmorphism dark dashboard with:
- Left sticky sidebar with 6 nav items
- KPI cards with coloured top bars and neon glow numbers
- Chart.js donut, bar, pie, gauge charts
- Colourful background with animated orbs
- Each section has a unique accent colour
```
**Why it worked:** Specific visual requirements produced targeted CSS instead of generic styling.

---

### Prompt 3 — Pytest Happy Path
```
Write pytest tests for a Flask app covering:
- Happy path with valid CSV and JSON upload (Gemini mocked)
- Route returns 200 status
- handover_note.md saved to disk
- Chart data present in HTML response
Use monkeypatch to mock the Gemini model so no real API is called
```
**Why it worked:** Explicitly asking for `monkeypatch` mock prevented real API calls in tests.

---

### Prompt 4 — Time Parser
```
Write a Python function parse_time_str() that:
1. Accepts HH:MM format and returns today's datetime
2. If HH:MM is in the future (overnight shift), subtract 1 day
3. Falls back to pd.to_datetime() for ISO format
4. Falls back to datetime.now() if all else fails
```
**Why it worked:** Clear step-by-step requirements produced clean, edge-case-safe code.

---

## Summary

| Category | Count |
|---|---|
| Features AI helped build | 5 major features |
| Bugs AI introduced | 5 bugs |
| Bugs fixed with AI help | 5 bugs |
| Pytest tests generated | 43 tests |
| Tests passing | 43 / 43 ✅ |
| Best prompts | 4 key prompts |

> AI was most useful for boilerplate generation, UI CSS, and test structure.
> Manual debugging was needed for file paths, Git issues, and API key security.
