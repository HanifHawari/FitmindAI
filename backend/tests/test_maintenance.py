"""Mode maintenance: server tetap melayani saat database (Neon) tidak bisa diakses."""
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient
from sqlalchemy.exc import OperationalError

from database.db_engine import get_db
from main import app


def unavailable_db():
    raise OperationalError("SELECT 1", {}, Exception("compute time quota exceeded"))
    yield  # pragma: no cover - menjadikan fungsi ini dependency generator


class MaintenanceTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def tearDown(self):
        self.client.close()
        app.dependency_overrides.clear()

    def test_database_error_returns_maintenance_503(self):
        app.dependency_overrides[get_db] = unavailable_db
        with patch("main.mark_database") as mark:
            response = self.client.post("/api/users/login", json={"username": "budi", "password": "Password123!"})
        self.assertEqual(response.status_code, 503)
        self.assertTrue(response.json()["maintenance"])
        mark.assert_called_once_with(False)

    def test_status_reports_maintenance_when_database_down(self):
        with patch("routers.status.database_available", return_value=False):
            data = self.client.get("/api/status").json()
        self.assertEqual(data["status"], "maintenance")
        self.assertEqual(data["reason"], "database")
        self.assertFalse(data["database"])

    def test_status_ok_when_database_ready(self):
        with patch("routers.status.database_available", return_value=True), \
             patch("routers.status.database_prepared", return_value=True):
            data = self.client.get("/api/status").json()
        self.assertEqual(data["status"], "ok")
        self.assertTrue(data["database"])

    def test_status_waits_until_database_is_prepared(self):
        with patch("routers.status.database_available", return_value=True), \
             patch("routers.status.database_prepared", return_value=False), \
             patch("routers.status.prepare_database_in_background") as prepare:
            data = self.client.get("/api/status").json()
        self.assertEqual(data["status"], "maintenance")
        prepare.assert_called_once()

    def test_manual_maintenance_mode(self):
        with patch("routers.status.MAINTENANCE_MODE", True), \
             patch("routers.status.database_available") as check:
            data = self.client.get("/api/status").json()
        self.assertEqual(data["status"], "maintenance")
        self.assertEqual(data["reason"], "planned")
        check.assert_not_called()

    def test_health_does_not_touch_database(self):
        with patch("database.status.database_available") as check:
            response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        check.assert_not_called()


if __name__ == "__main__":
    unittest.main()
