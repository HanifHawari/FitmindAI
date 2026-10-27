"""Regression checks for account isolation and static-file boundaries."""
import asyncio
import base64
import unittest
from pathlib import Path

from fastapi import HTTPException
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from database.db_engine import get_db, init_db
from database.db_models import Base
from main import app, serve_spa


class SecurityTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
        Base.metadata.create_all(self.engine)
        session_factory = sessionmaker(bind=self.engine)

        def test_db():
            with session_factory() as db:
                yield db

        app.dependency_overrides[get_db] = test_db
        self.client = TestClient(app)

    def tearDown(self):
        self.client.close()
        app.dependency_overrides.clear()
        self.engine.dispose()

    def _register_and_login(self, username):
        credentials = {"username": username, "password": "Password123!", "phone": "081234567890"}
        self.assertEqual(self.client.post("/api/users/register", json=credentials).status_code, 200)
        response = self.client.post("/api/users/login", json=credentials)
        self.assertEqual(response.status_code, 200)
        return {"Authorization": f"Bearer {response.json()['token']}"}

    def test_private_data_requires_matching_account(self):
        alice = self._register_and_login("alice")
        bob = self._register_and_login("bob")
        self.assertEqual(self.client.get("/api/users/alice/profile").status_code, 401)
        self.assertEqual(self.client.get("/api/users/alice/profile", headers=bob).status_code, 403)
        self.assertEqual(self.client.get("/api/users/alice/profile", headers=alice).status_code, 200)
        self.assertEqual(self.client.get("/api/users/me", headers=alice).json()["username"], "alice")
        self.assertEqual(self.client.post("/api/chat/session", json={"username": "bob", "message": "halo"}, headers=alice).status_code, 403)
        self.assertEqual(self.client.post("/api/chat", json={"message": "halo"}).status_code, 401)
        self.assertEqual(self.client.post("/api/chat/stream", json={"message": "halo"}).status_code, 401)
        self.assertEqual(self.client.post("/api/plans/generate", json={}).status_code, 401)
        self.assertEqual(self.client.post("/api/whatsapp/send-plan", json={"phone": "081234567890", "plan_type": "workout", "title": "A"}).status_code, 401)
        self.assertEqual(self.client.get("/api/workout/gif/all").status_code, 401)

    def test_avatar_is_private_and_persists_until_removed(self):
        alice = self._register_and_login("alice")
        bob = self._register_and_login("bob")
        image = Path(__file__).resolve().parents[2] / "frontend" / "public" / "foto1.jpg"
        data_url = "data:image/jpeg;base64," + base64.b64encode(image.read_bytes()).decode("ascii")

        self.assertEqual(self.client.put("/api/users/me/avatar", json={"data_url": data_url}).status_code, 401)
        self.assertEqual(self.client.put("/api/users/me/avatar", json={"data_url": "data:image/png;base64,AAAA"}, headers=alice).status_code, 400)
        response = self.client.put("/api/users/me/avatar", json={"data_url": data_url}, headers=alice)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.client.get("/api/users/me", headers=alice).json()["avatar_data"], data_url)
        self.assertIsNone(self.client.get("/api/users/me", headers=bob).json()["avatar_data"])
        self.assertEqual(self.client.delete("/api/users/me/avatar", headers=alice).status_code, 200)
        self.assertIsNone(self.client.get("/api/users/me", headers=alice).json()["avatar_data"])

    def test_avatar_column_is_added_to_existing_database(self):
        from unittest.mock import patch
        from database import db_engine

        legacy_engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
        try:
            with legacy_engine.begin() as connection:
                connection.exec_driver_sql("CREATE TABLE users (id INTEGER PRIMARY KEY, username VARCHAR(100) NOT NULL)")
            with patch.object(db_engine, "engine", legacy_engine):
                init_db()
                init_db()
            self.assertIn("avatar_data", {column["name"] for column in inspect(legacy_engine).get_columns("users")})
        finally:
            legacy_engine.dispose()

    def test_invalid_token_and_path_are_rejected(self):
        alice = self._register_and_login("alice")
        forged = {"Authorization": alice["Authorization"] + "x"}
        self.assertEqual(self.client.get("/api/users/me", headers=forged).status_code, 401)
        with self.assertRaises(HTTPException) as error:
            asyncio.run(serve_spa("../.env"))
        self.assertEqual(error.exception.status_code, 404)

    def test_workout_dataset_routes_handle_empty_database(self):
        self.assertEqual(self.client.get("/api/workout/body-parts").json()["data"], [])
        self.assertEqual(self.client.get("/api/workout/muscles").json()["data"], [])
        response = self.client.get("/api/workout/generate-split")
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json()["success"])

    def test_whatsapp_plan_limits_nested_content(self):
        alice = self._register_and_login("alice")
        oversized_day = {"day": "Senin", "focus": "Kekuatan", "exercises": [
            {"name": "Push up", "sets": 3, "reps": "10"} for _ in range(31)
        ]}
        response = self.client.post("/api/whatsapp/send-plan", json={
            "plan_type": "workout", "title": "Program", "schedule": [oversized_day]
        }, headers=alice)
        self.assertEqual(response.status_code, 422)

    def test_register_accepts_only_a_single_phone_number(self):
        for phone in ("0812345678,0813456789", "08123", "abc12345678"):
            response = self.client.post("/api/users/register", json={"username": "eve", "password": "Password123!", "phone": phone})
            self.assertEqual(response.status_code, 400)
        response = self.client.post("/api/users/register", json={"username": "eve", "password": "Password123!", "phone": "+62 812-3456-7890"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["phone"], "+6281234567890")

    def test_whatsapp_rejects_stored_phone_lists(self):
        from unittest.mock import patch
        from database.db_models import User

        alice = self._register_and_login("alice")
        with sessionmaker(bind=self.engine)() as db:
            db.query(User).filter(User.username == "alice").update({"phone": "0812345678,0813456789"})
            db.commit()
        with patch("routers.whatsapp.FONNTE_TOKEN", "test-token"):
            response = self.client.post("/api/whatsapp/send-plan", json={"plan_type": "workout", "title": "A"}, headers=alice)
        self.assertEqual(response.status_code, 400)

    def test_login_is_throttled_after_repeated_failures(self):
        from routers import users

        self._register_and_login("mallory")
        try:
            for _ in range(10):
                response = self.client.post("/api/users/login", json={"username": "mallory", "password": "salah-salah"})
                self.assertEqual(response.status_code, 401)
            response = self.client.post("/api/users/login", json={"username": "mallory", "password": "Password123!"})
            self.assertEqual(response.status_code, 429)
        finally:
            users._login_failures.reset("mallory")

    def test_calendar_export_requires_login_and_tolerates_bad_times(self):
        plan = {"plan_type": "meal", "title": "Menu", "meals": [
            {"meal_name": "Sarapan", "time": "25:99", "foods": [{"name": "Oat", "portion": "100g", "calories": 350.5}]}
        ]}
        self.assertEqual(self.client.post("/api/calendar/export", json=plan).status_code, 401)
        alice = self._register_and_login("alice")
        response = self.client.post("/api/calendar/export", json=plan, headers=alice)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"BEGIN:VCALENDAR", response.content)

    def test_profile_values_must_fit_database_columns(self):
        alice = self._register_and_login("alice")
        self.assertEqual(self.client.put("/api/users/alice/profile", json={"gender": "x" * 11}, headers=alice).status_code, 422)
        self.assertEqual(self.client.put("/api/users/alice/profile", json={"age": 25, "gender": "Male"}, headers=alice).status_code, 200)

    def test_chat_history_accepts_long_ai_answers(self):
        from models import ChatRequestDB

        request = ChatRequestDB(username="alice", message="lanjut", history=[{"role": "assistant", "content": "x" * 5000}])
        self.assertEqual(len(request.history[0].content), 5000)

    def test_exercise_requests_cannot_escape_their_endpoint(self):
        from exercise_api import _segment, is_valid_exercise_id

        self.assertEqual(_segment("../exercise/0001"), "..%2Fexercise%2F0001")
        self.assertFalse(is_valid_exercise_id("../image"))
        self.assertTrue(is_valid_exercise_id("0001"))
        self.assertEqual(self.client.get("/api/workout/gif/image/..%2F..%2Fstatus").status_code, 404)


if __name__ == "__main__":
    unittest.main()
