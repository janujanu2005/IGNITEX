import os
import unittest
from app import app, parse_time_str
from datetime import datetime, timedelta

class TestShiftHandover(unittest.TestCase):
    def setUp(self):
        app.config["TESTING"] = True
        self.client = app.test_client()
        self.workspace_dir = os.path.abspath(os.path.dirname(__file__))
        self.discord_path = os.path.join(self.workspace_dir, "discord.json")
        self.tickets_path = os.path.join(self.workspace_dir, "tickets.csv")

    def test_parse_time_str(self):
        print("\n--- Testing Time Parsing ---")
        now = datetime.now()
        # Test HH:MM format (e.g. today's time)
        time_str = (now - timedelta(hours=2)).strftime("%H:%M")
        parsed = parse_time_str(time_str)
        print(f"Current time: {now.strftime('%H:%M')}, Input time: {time_str}, Parsed: {parsed}")
        self.assertEqual(parsed.hour, (now - timedelta(hours=2)).hour)
        self.assertEqual(parsed.minute, (now - timedelta(hours=2)).minute)

        # Test yesterday's time (future hour value)
        future_time = (now + timedelta(hours=2))
        time_str_future = future_time.strftime("%H:%M")
        parsed_future = parse_time_str(time_str_future)
        print(f"Current time: {now.strftime('%H:%M')}, Future input time: {time_str_future}, Parsed (should be yesterday): {parsed_future}")
        # Difference should be roughly 22 hours in the past
        diff = now - parsed_future
        self.assertTrue(timedelta(hours=21) < diff < timedelta(hours=23))

    def test_generate_endpoint_upload_mode(self):
        print("\n--- Testing /generate Endpoint in Upload Mode ---")
        if not os.path.exists(self.discord_path) or not os.path.exists(self.tickets_path):
            self.skipTest("Missing discord.json or tickets.csv in workspace")

        # Open files to upload
        with open(self.discord_path, "rb") as discord_f, open(self.tickets_path, "rb") as tickets_f:
            data = {
                "discord_mode": "upload",
                "discord": (discord_f, "discord.json"),
                "tickets": (tickets_f, "tickets.csv")
            }
            try:
                response = self.client.post("/generate", data=data, content_type="multipart/form-data")
                
                print(f"Generate response status: {response.status_code}")
                self.assertEqual(response.status_code, 200)
                
                # Check if handover_note.md was created in root
                self.assertTrue(os.path.exists("handover_note.md"))
                with open("handover_note.md", "r", encoding="utf-8") as f:
                    content = f.read()
                
                print("Generated handover note content length:", len(content))
                
                # Validate headers are present in the output
                self.assertIn("### 1. High Priority Unresolved Fires", content)
                self.assertIn("### 2. General System Fixes Delivered", content)
                self.assertIn("### 3. Critical Infrastructure Monitor Watchlist", content)
            except Exception as e:
                if "quota" in str(e).lower() or "exhausted" in str(e).lower() or "429" in str(e):
                    self.skipTest(f"Gemini API Quota Limit Exceeded: {str(e)}")
                else:
                    raise

    def test_generate_endpoint_live_mode_invalid_auth(self):
        print("\n--- Testing /generate Endpoint in Live Mode (Invalid Credentials) ---")
        if not os.path.exists(self.tickets_path):
            self.skipTest("Missing tickets.csv in workspace")

        with open(self.tickets_path, "rb") as tickets_f:
            data = {
                "discord_mode": "live",
                "bot_token": "dummy_invalid_token_12345",
                "channel_id": "1152197303102425088",
                "tickets": (tickets_f, "tickets.csv")
            }
            response = self.client.post("/generate", data=data, content_type="multipart/form-data")
            
            # Should load homepage with error notification
            print(f"Generate response status: {response.status_code}")
            self.assertEqual(response.status_code, 200)
            
            html_content = response.data.decode("utf-8")
            self.assertIn("Discord API Error 401", html_content)
            print("Live mode invalid token error successfully caught and displayed in UI.")

    def test_download_endpoint(self):
        print("\n--- Testing Download Endpoint ---")
        # Ensure the file exists
        if not os.path.exists("handover_note.md"):
            with open("handover_note.md", "w", encoding="utf-8") as f:
                f.write("test content")

        response = self.client.get("/output/handover_note.md")
        print(f"Download response status: {response.status_code}")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers.get("Content-Disposition"), "attachment; filename=handover_note.md")

if __name__ == "__main__":
    unittest.main()