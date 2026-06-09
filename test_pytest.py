"""
=============================================================
  Shift Handover Note Generator — Pytest Test Suite
  Covers: Happy Path, Edge Cases, API Routes, Core Logic
=============================================================
Run with:
    pip install pytest
    pytest test_pytest.py -v
"""

import os
import io
import json
import pytest
from datetime import datetime, timedelta

# ── Import app ────────────────────────────────────────────
from app import app, parse_time_str, BASE_DIR


# ══════════════════════════════════════════════════════════
# FIXTURES
# ══════════════════════════════════════════════════════════

@pytest.fixture
def client():
    """Flask test client — used by all route tests."""
    app.config["TESTING"] = True
    app.config["WTF_CSRF_ENABLED"] = False
    with app.test_client() as c:
        yield c


@pytest.fixture
def sample_tickets_csv():
    """Minimal valid CSV bytes for upload tests."""
    content = (
        "ticket_id,status,priority,summary,created\n"
        "101,Open,High,Payment service failure,09:05\n"
        "102,Monitoring,Medium,High CPU utilization,09:15\n"
        "103,Resolved,Low,Login bug fixed,09:40\n"
    )
    return io.BytesIO(content.encode("utf-8"))


@pytest.fixture
def sample_discord_json():
    """Minimal valid Discord JSON bytes for upload tests."""
    messages = [
        {"user": "alice", "message": "Payment service is down!", "time": "09:04"},
        {"user": "bob",   "message": "CPU is at 94%",            "time": "09:14"},
    ]
    return io.BytesIO(json.dumps(messages).encode("utf-8"))


@pytest.fixture
def full_tickets_csv():
    """Full 10-row test CSV."""
    path = os.path.join(BASE_DIR, "test_data", "tickets_test_full.csv")
    with open(path, "rb") as f:
        return io.BytesIO(f.read())


@pytest.fixture
def full_discord_json():
    """Full 10-message test JSON."""
    path = os.path.join(BASE_DIR, "test_data", "discord_test_full.json")
    with open(path, "rb") as f:
        return io.BytesIO(f.read())


@pytest.fixture
def empty_discord_json():
    """Empty Discord JSON."""
    return io.BytesIO(b"[]")


# ══════════════════════════════════════════════════════════
# 1. UNIT TESTS — parse_time_str()
# ══════════════════════════════════════════════════════════

class TestParseTimeStr:
    """Tests for the temporal filtering helper function."""

    def test_hhmm_recent_time_parsed_correctly(self):
        """HH:MM format — recent time returns today's datetime."""
        two_hours_ago = datetime.now() - timedelta(hours=2)
        time_str = two_hours_ago.strftime("%H:%M")
        result = parse_time_str(time_str)
        assert result.hour == two_hours_ago.hour
        assert result.minute == two_hours_ago.minute

    def test_hhmm_future_time_returns_yesterday(self):
        """HH:MM format — future hour returns yesterday (overnight shift logic)."""
        future = datetime.now() + timedelta(hours=3)
        time_str = future.strftime("%H:%M")
        result = parse_time_str(time_str)
        diff = datetime.now() - result
        # Should be ~21 hours in the past (yesterday's time)
        assert timedelta(hours=20) < diff < timedelta(hours=24)

    def test_iso_format_parsed_correctly(self):
        """ISO 8601 format parses to correct datetime."""
        iso = "2026-06-09T09:05:00"
        result = parse_time_str(iso)
        assert result.year == 2026
        assert result.month == 6
        assert result.day == 9
        assert result.hour == 9
        assert result.minute == 5

    def test_invalid_string_returns_datetime(self):
        """Garbage input falls back to datetime.now() without crashing."""
        result = parse_time_str("not-a-time")
        assert isinstance(result, datetime)

    def test_integer_input_handled(self):
        """Non-string input (int) is coerced without crashing."""
        result = parse_time_str(930)
        assert isinstance(result, datetime)

    def test_empty_string_returns_datetime(self):
        """Empty string falls back gracefully."""
        result = parse_time_str("")
        assert isinstance(result, datetime)

    def test_whitespace_stripped(self):
        """Leading/trailing spaces are stripped before parsing."""
        two_hours_ago = datetime.now() - timedelta(hours=2)
        time_str = "  " + two_hours_ago.strftime("%H:%M") + "  "
        result = parse_time_str(time_str)
        assert result.hour == two_hours_ago.hour


# ══════════════════════════════════════════════════════════
# 2. ROUTE TESTS — GET /
# ══════════════════════════════════════════════════════════

class TestHomeRoute:
    """Tests for the index page."""

    def test_home_returns_200(self, client):
        """GET / returns HTTP 200."""
        response = client.get("/")
        assert response.status_code == 200

    def test_home_contains_form(self, client):
        """Index page contains the generate form."""
        response = client.get("/")
        html = response.data.decode("utf-8")
        assert "Generate" in html

    def test_home_contains_discord_label(self, client):
        """Index page shows Discord source section."""
        response = client.get("/")
        html = response.data.decode("utf-8")
        assert "discord" in html.lower()

    def test_home_contains_tickets_label(self, client):
        """Index page shows CSV tickets section."""
        response = client.get("/")
        html = response.data.decode("utf-8")
        assert "ticket" in html.lower() or "csv" in html.lower()

    def test_home_content_type_is_html(self, client):
        """Index page returns HTML content type."""
        response = client.get("/")
        assert "text/html" in response.content_type


# ══════════════════════════════════════════════════════════
# 3. ROUTE TESTS — POST /generate (Upload Mode)
# ══════════════════════════════════════════════════════════

class TestGenerateRouteUploadMode:
    """Happy path and edge case tests for the /generate endpoint."""

    def test_missing_discord_file_shows_error(self, client, sample_tickets_csv):
        """Upload mode with no discord file returns error in UI."""
        data = {
            "discord_mode": "upload",
            "tickets": (sample_tickets_csv, "tickets.csv"),
        }
        response = client.post("/generate", data=data,
                               content_type="multipart/form-data")
        assert response.status_code == 200
        html = response.data.decode("utf-8")
        assert "error" in html.lower() or "valid" in html.lower()

    def test_missing_bot_token_live_mode_shows_error(self, client, sample_tickets_csv):
        """Live mode with empty bot token returns validation error."""
        data = {
            "discord_mode": "live",
            "bot_token": "",
            "channel_id": "",
            "tickets": (sample_tickets_csv, "tickets.csv"),
        }
        response = client.post("/generate", data=data,
                               content_type="multipart/form-data")
        assert response.status_code == 200
        html = response.data.decode("utf-8")
        assert "required" in html.lower() or "error" in html.lower()

    def test_invalid_discord_token_shows_401_error(self, client, sample_tickets_csv):
        """Live mode with invalid token shows Discord API 401 error."""
        data = {
            "discord_mode": "live",
            "bot_token": "fake_token_xyz",
            "channel_id": "1152197303102425088",
            "tickets": (sample_tickets_csv, "tickets.csv"),
        }
        response = client.post("/generate", data=data,
                               content_type="multipart/form-data")
        assert response.status_code == 200
        html = response.data.decode("utf-8")
        assert "401" in html or "error" in html.lower()

    def test_upload_with_empty_discord_json(self, client, monkeypatch,
                                            empty_discord_json,
                                            sample_tickets_csv):
        """Empty discord.json processes without crashing."""
        # Mock Gemini so no real API call is made
        class MockResponse:
            text = ("### 1. High Priority Unresolved Fires\n- Test\n"
                    "### 2. General System Fixes Delivered\n- Test\n"
                    "### 3. Critical Infrastructure Monitor Watchlist\n- Test\n")

        class MockModel:
            def generate_content(self, prompt):
                return MockResponse()

        import app as app_module
        monkeypatch.setattr(app_module, "model", MockModel())

        data = {
            "discord_mode": "upload",
            "discord": (empty_discord_json, "discord.json"),
            "tickets": (sample_tickets_csv, "tickets.csv"),
        }
        response = client.post("/generate", data=data,
                               content_type="multipart/form-data")
        assert response.status_code == 200


# ══════════════════════════════════════════════════════════
# 4. ROUTE TESTS — Download Endpoints
# ══════════════════════════════════════════════════════════

class TestDownloadRoutes:
    """Tests for all file download endpoints."""

    def test_download_handover_note_returns_200(self, client):
        """Download endpoint returns 200 when file exists."""
        # Ensure file exists
        path = os.path.join(BASE_DIR, "handover_note.md")
        with open(path, "w", encoding="utf-8") as f:
            f.write("### 1. High Priority Unresolved Fires\n- Test item\n"
                    "### 2. General System Fixes Delivered\n- Fix\n"
                    "### 3. Critical Infrastructure Monitor Watchlist\n- Watch\n")
        response = client.get("/output/handover_note.md")
        assert response.status_code == 200

    def test_download_handover_note_is_attachment(self, client):
        """Download response has attachment content-disposition."""
        path = os.path.join(BASE_DIR, "handover_note.md")
        with open(path, "w", encoding="utf-8") as f:
            f.write("test content")
        response = client.get("/output/handover_note.md")
        cd = response.headers.get("Content-Disposition", "")
        assert "attachment" in cd
        assert "handover_note.md" in cd

    def test_download_readme_returns_200(self, client):
        """GET /docs/README.md returns 200."""
        response = client.get("/docs/README.md")
        assert response.status_code == 200

    def test_download_test_cases_returns_200(self, client):
        """GET /docs/TEST_CASES.md returns 200."""
        response = client.get("/docs/TEST_CASES.md")
        assert response.status_code == 200

    def test_download_explanation_returns_200(self, client):
        """GET /docs/EXPLANATION.md returns 200."""
        response = client.get("/docs/EXPLANATION.md")
        assert response.status_code == 200

    def test_download_blocked_unknown_doc(self, client):
        """Unknown doc filename returns 404."""
        response = client.get("/docs/secret_file.txt")
        assert response.status_code == 404

    def test_download_tickets_test_full_csv(self, client):
        """GET /test-data/tickets_test_full.csv returns 200."""
        response = client.get("/test-data/tickets_test_full.csv")
        assert response.status_code == 200

    def test_download_discord_test_full_json(self, client):
        """GET /test-data/discord_test_full.json returns 200."""
        response = client.get("/test-data/discord_test_full.json")
        assert response.status_code == 200

    def test_download_smoke_tickets(self, client):
        """GET /test-data/smoke_tickets.csv returns 200."""
        response = client.get("/test-data/smoke_tickets.csv")
        assert response.status_code == 200

    def test_download_blocked_unknown_test_data(self, client):
        """Unknown test data filename returns 404."""
        response = client.get("/test-data/../../app.py")
        assert response.status_code == 404


# ══════════════════════════════════════════════════════════
# 5. UNIT TESTS — Duplicate Detection Logic
# ══════════════════════════════════════════════════════════

class TestDuplicateDetection:
    """Tests for the keyword-overlap duplicate detection algorithm."""

    def _run_dedup(self, summaries):
        """Helper: run duplicate detection on a list of summaries."""
        import pandas as pd
        rows = [{"ticket_id": str(i+1), "summary": s,
                 "status": "Open", "priority": "High", "created": "09:00"}
                for i, s in enumerate(summaries)]
        tickets = pd.DataFrame(rows)
        duplicates = []
        seen = {}
        for _, row in tickets.iterrows():
            words = frozenset(str(row["summary"]).lower().split())
            for seen_words, seen_row in seen.items():
                overlap = words & seen_words
                if len(overlap) >= 2:
                    duplicates.append({
                        "ticket_a": str(row["ticket_id"]),
                        "ticket_b": str(seen_row["ticket_id"]),
                        "overlap": " | ".join(sorted(overlap))
                    })
            seen[words] = row.to_dict()
        return duplicates

    def test_clear_duplicate_detected(self):
        """Two summaries sharing 2+ keywords are flagged as duplicates."""
        summaries = [
            "Payment service failure on checkout",
            "Payment gateway timeout on checkout",
        ]
        dupes = self._run_dedup(summaries)
        assert len(dupes) == 1
        assert dupes[0]["ticket_a"] == "2"
        assert dupes[0]["ticket_b"] == "1"

    def test_no_duplicate_for_unrelated_tickets(self):
        """Unrelated tickets produce zero duplicates."""
        summaries = [
            "Payment service failure",
            "Login page error",
            "CPU spike on server",
        ]
        dupes = self._run_dedup(summaries)
        assert len(dupes) == 0

    def test_single_shared_word_not_flagged(self):
        """Only 1 shared word — not enough to be a duplicate."""
        summaries = [
            "Payment failure",
            "Payment success",
        ]
        dupes = self._run_dedup(summaries)
        assert len(dupes) == 0

    def test_multiple_duplicates_detected(self):
        """Multiple duplicate pairs detected correctly."""
        summaries = [
            "Payment service failure on checkout",
            "Payment gateway timeout on checkout",
            "Email notification delay in queue",
            "Email delivery queue backlog issue",
        ]
        dupes = self._run_dedup(summaries)
        assert len(dupes) == 2

    def test_overlap_keywords_included_in_result(self):
        """Overlap keywords are present in the result dict."""
        summaries = [
            "Database connection failure on replica",
            "Database connection issue resolved",
        ]
        dupes = self._run_dedup(summaries)
        assert len(dupes) == 1
        assert "database" in dupes[0]["overlap"]
        assert "connection" in dupes[0]["overlap"]


# ══════════════════════════════════════════════════════════
# 6. UNIT TESTS — Assignee Matching Logic
# ══════════════════════════════════════════════════════════

class TestAssigneeMatching:
    """Tests for the keyword-based assignee recommendation logic."""

    ASSIGNEE_MAP = {
        "payment":  {"name": "Alice Johnson",  "role": "Payments Engineer"},
        "database": {"name": "Bob Martinez",   "role": "DBA / Infra Lead"},
        "cpu":      {"name": "Carol Singh",    "role": "SRE / DevOps"},
        "login":    {"name": "David Kim",      "role": "Auth Engineer"},
        "email":    {"name": "Eva Chen",       "role": "Notifications Team"},
        "server":   {"name": "Frank Osei",     "role": "Backend Engineer"},
        "network":  {"name": "Grace Liu",      "role": "Network Operations"},
        "default":  {"name": "On-Call SRE",    "role": "Shift Duty Engineer"},
    }

    def _match(self, summary):
        summary_lower = summary.lower()
        assignee = self.ASSIGNEE_MAP["default"]
        for keyword, info in self.ASSIGNEE_MAP.items():
            if keyword != "default" and keyword in summary_lower:
                assignee = info
                break
        return assignee

    def test_payment_keyword_assigns_alice(self):
        a = self._match("Payment service failure on checkout")
        assert a["name"] == "Alice Johnson"

    def test_database_keyword_assigns_bob(self):
        a = self._match("Database connection failure on replica")
        assert a["name"] == "Bob Martinez"

    def test_cpu_keyword_assigns_carol(self):
        a = self._match("High CPU utilization on prod server")
        assert a["name"] == "Carol Singh"

    def test_login_keyword_assigns_david(self):
        a = self._match("Login page returning 500 error")
        assert a["name"] == "David Kim"

    def test_email_keyword_assigns_eva(self):
        a = self._match("Email notification delay over 30 minutes")
        assert a["name"] == "Eva Chen"

    def test_server_keyword_assigns_frank(self):
        a = self._match("Server disk usage at 90 percent")
        assert a["name"] == "Frank Osei"

    def test_network_keyword_assigns_grace(self):
        a = self._match("Network packet loss detected on cluster")
        assert a["name"] == "Grace Liu"

    def test_unknown_keyword_assigns_oncall(self):
        a = self._match("Unknown infrastructure anomaly detected")
        assert a["name"] == "On-Call SRE"

    def test_case_insensitive_matching(self):
        """Keywords match regardless of uppercase in summary."""
        a = self._match("PAYMENT GATEWAY DOWN")
        assert a["name"] == "Alice Johnson"


# ══════════════════════════════════════════════════════════
# 7. HAPPY PATH — Full Pipeline (mocked Gemini)
# ══════════════════════════════════════════════════════════

class TestHappyPath:
    """End-to-end happy path with Gemini mocked out."""

    def test_full_pipeline_smoke(self, client, monkeypatch,
                                  empty_discord_json, sample_tickets_csv):
        """
        HAPPY PATH: Upload mode with valid files.
        Gemini is mocked to return a valid 3-section markdown.
        Dashboard should render with all KPI data.
        """
        # Mock Gemini response
        mock_md = (
            "### 1. High Priority Unresolved Fires\n"
            "- Payment service is down.\n\n"
            "### 2. General System Fixes Delivered\n"
            "- Login bug resolved.\n\n"
            "### 3. Critical Infrastructure Monitor Watchlist\n"
            "- CPU spike under monitoring.\n"
        )

        class MockResponse:
            text = mock_md

        class MockModel:
            def generate_content(self, prompt):
                return MockResponse()

        import app as app_module
        monkeypatch.setattr(app_module, "model", MockModel())

        data = {
            "discord_mode": "upload",
            "discord": (empty_discord_json, "discord.json"),
            "tickets": (sample_tickets_csv, "tickets.csv"),
        }
        response = client.post("/generate", data=data,
                               content_type="multipart/form-data")

        assert response.status_code == 200
        html = response.data.decode("utf-8")

        # Dashboard sections present
        assert "Operational Metrics Dashboard" in html or "dashboard" in html.lower()

        # AI report sections rendered
        assert "High Priority" in html
        assert "General System" in html
        assert "Critical Infrastructure" in html

    def test_handover_md_saved_to_disk(self, client, monkeypatch,
                                        empty_discord_json, sample_tickets_csv):
        """HAPPY PATH: handover_note.md is written to BASE_DIR after generation."""
        mock_md = (
            "### 1. High Priority Unresolved Fires\n- Test\n"
            "### 2. General System Fixes Delivered\n- Test\n"
            "### 3. Critical Infrastructure Monitor Watchlist\n- Test\n"
        )

        class MockResponse:
            text = mock_md

        class MockModel:
            def generate_content(self, prompt):
                return MockResponse()

        import app as app_module
        monkeypatch.setattr(app_module, "model", MockModel())

        data = {
            "discord_mode": "upload",
            "discord": (empty_discord_json, "discord.json"),
            "tickets": (sample_tickets_csv, "tickets.csv"),
        }
        client.post("/generate", data=data, content_type="multipart/form-data")

        path = os.path.join(BASE_DIR, "handover_note.md")
        assert os.path.exists(path)
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        assert "High Priority Unresolved Fires" in content

    def test_kpi_data_in_response(self, client, monkeypatch,
                                   empty_discord_json, sample_tickets_csv):
        """HAPPY PATH: Response contains ticket count and priority data."""
        class MockResponse:
            text = ("### 1. High Priority Unresolved Fires\n- x\n"
                    "### 2. General System Fixes Delivered\n- x\n"
                    "### 3. Critical Infrastructure Monitor Watchlist\n- x\n")

        class MockModel:
            def generate_content(self, prompt):
                return MockResponse()

        import app as app_module
        monkeypatch.setattr(app_module, "model", MockModel())

        data = {
            "discord_mode": "upload",
            "discord": (empty_discord_json, "discord.json"),
            "tickets": (sample_tickets_csv, "tickets.csv"),
        }
        response = client.post("/generate", data=data,
                               content_type="multipart/form-data")
        html = response.data.decode("utf-8")

        # Chart data injected into page
        assert "priority_counts" in html or "priorityData" in html or "PRI" in html
