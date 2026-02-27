import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


class TestHealthCheck:
    def test_health_returns_ok(self):
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "mode" in data


class TestEventsRouter:
    def test_list_events_empty(self):
        response = client.get("/api/events")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_get_event_not_found(self):
        response = client.get("/api/events/nonexistent")
        assert response.status_code == 404


class TestPeopleRouter:
    def test_list_people_empty(self):
        response = client.get("/api/people")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_get_person_not_found(self):
        response = client.get("/api/people/nonexistent")
        assert response.status_code == 404


class TestProfileRouter:
    def test_get_profile_empty(self):
        response = client.get("/api/profile")
        assert response.status_code == 200

    def test_update_profile(self):
        response = client.put(
            "/api/profile",
            json={"name": "John Park", "role": "Founder"},
        )
        assert response.status_code == 200
        assert response.json()["name"] == "John Park"

    def test_get_preferences_defaults(self):
        response = client.get("/api/profile/preferences")
        assert response.status_code == 200
        prefs = response.json()
        assert prefs["topic_weight"] == 30
        assert prefs["people_weight"] == 25


class TestTargetsRouter:
    def test_list_targets_empty(self):
        response = client.get("/api/targets")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_create_target(self):
        response = client.post(
            "/api/targets",
            json={
                "name": "Sam Altman",
                "company": "OpenAI",
                "reason": "Discuss fundraising",
                "priority": "high",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Sam Altman"
        assert data["status"] == "searching"
        assert data["priority"] == "high"

    def test_delete_target_not_found(self):
        response = client.delete("/api/targets/nonexistent")
        assert response.status_code == 404


class TestFeedbackRouter:
    def test_submit_feedback(self):
        response = client.post(
            "/api/feedback",
            json={"action": "reject", "reason": "not_my_industry"},
        )
        assert response.status_code == 201

    def test_get_feedback_stats(self):
        response = client.get("/api/feedback/stats")
        assert response.status_code == 200
        assert "total_feedback" in response.json()


class TestAgentRouter:
    def test_get_status(self):
        response = client.get("/api/agent/status")
        assert response.status_code == 200
        assert "status" in response.json()

    def test_pause_agent(self):
        response = client.post("/api/agent/pause")
        assert response.status_code == 200
        assert response.json()["status"] == "paused"

    def test_resume_agent(self):
        response = client.post("/api/agent/resume")
        assert response.status_code == 200
        assert response.json()["status"] == "running"


class TestWebhooks:
    def test_yutori_new_event(self):
        response = client.post(
            "/webhooks/yutori/new-event",
            json={"event": "test"},
        )
        assert response.status_code == 200

    def test_yutori_apply_result(self):
        response = client.post(
            "/webhooks/yutori/apply-result",
            json={"task_id": "t-123", "status": "succeeded"},
        )
        assert response.status_code == 200
