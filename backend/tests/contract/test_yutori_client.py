from __future__ import annotations

import httpx
import pytest
import respx

from app.integrations.yutori_client import YutoriClient, YutoriTask

BASE_URL = "https://api.yutori.com"


# -- Fixtures ------------------------------------------------------------------


@pytest.fixture
def browsing_response() -> dict:
    return {
        "task_id": "browse-123",
        "status": "running",
        "result": None,
    }


@pytest.fixture
def scouting_response() -> dict:
    return {
        "task_id": "scout-456",
        "status": "scheduled",
        "result": None,
    }


@pytest.fixture
def completed_response() -> dict:
    return {
        "task_id": "browse-123",
        "status": "completed",
        "result": {"applied": True, "confirmation": "RSVP confirmed"},
    }


# -- Unit tests ----------------------------------------------------------------


class TestYutoriTask:
    def test_from_response_full(self, browsing_response: dict) -> None:
        task = YutoriTask.from_response(browsing_response)
        assert task.task_id == "browse-123"
        assert task.status == "running"
        assert task.result is None

    def test_from_response_completed(self, completed_response: dict) -> None:
        task = YutoriTask.from_response(completed_response)
        assert task.status == "completed"
        assert task.result is not None
        assert task.result["applied"] is True

    def test_from_response_missing_fields(self) -> None:
        task = YutoriTask.from_response({})
        assert task.task_id == ""
        assert task.status == "unknown"
        assert task.result is None


class TestYutoriClientInit:
    def test_requires_api_key(self) -> None:
        with pytest.raises(ValueError, match="yutori_api_key is required"):
            YutoriClient(api_key="")


class TestYutoriBrowsing:
    @respx.mock
    @pytest.mark.asyncio
    async def test_browsing_create_basic(self, browsing_response: dict) -> None:
        route = respx.post(f"{BASE_URL}/v1/browsing/tasks").mock(
            return_value=httpx.Response(200, json=browsing_response)
        )

        client = YutoriClient(api_key="yut-test-key")
        try:
            result = await client.browsing_create("Apply to AI dinner")

            assert route.called
            request = route.calls[0].request
            assert request.headers["X-API-Key"] == "yut-test-key"

            import json
            body = json.loads(request.content)
            assert body["task"] == "Apply to AI dinner"
            assert body["max_steps"] == 50
            assert "start_url" not in body

            assert result.task_id == "browse-123"
            assert result.status == "running"
        finally:
            await client.close()

    @respx.mock
    @pytest.mark.asyncio
    async def test_browsing_create_all_options(self, browsing_response: dict) -> None:
        route = respx.post(f"{BASE_URL}/v1/browsing/tasks").mock(
            return_value=httpx.Response(200, json=browsing_response)
        )

        client = YutoriClient(api_key="yut-test-key")
        try:
            await client.browsing_create(
                "Apply to AI dinner",
                start_url="https://lu.ma/ai-dinner",
                max_steps=100,
                output_schema={"applied": "boolean"},
                webhook_url="https://nexus.dev/webhook",
            )

            import json
            body = json.loads(route.calls[0].request.content)
            assert body["start_url"] == "https://lu.ma/ai-dinner"
            assert body["max_steps"] == 100
            assert body["output_schema"] == {"applied": "boolean"}
            assert body["webhook_url"] == "https://nexus.dev/webhook"
        finally:
            await client.close()

    @respx.mock
    @pytest.mark.asyncio
    async def test_browsing_get(self, completed_response: dict) -> None:
        route = respx.get(f"{BASE_URL}/v1/browsing/tasks/browse-123").mock(
            return_value=httpx.Response(200, json=completed_response)
        )

        client = YutoriClient(api_key="yut-test-key")
        try:
            result = await client.browsing_get("browse-123")

            assert route.called
            assert result.task_id == "browse-123"
            assert result.status == "completed"
            assert result.result["applied"] is True
        finally:
            await client.close()

    @respx.mock
    @pytest.mark.asyncio
    async def test_browsing_create_server_error(self) -> None:
        respx.post(f"{BASE_URL}/v1/browsing/tasks").mock(
            return_value=httpx.Response(500, json={"error": "internal"})
        )

        client = YutoriClient(api_key="yut-test-key")
        try:
            with pytest.raises(httpx.HTTPStatusError):
                await client.browsing_create("test task")
        finally:
            await client.close()


class TestYutoriScouting:
    @respx.mock
    @pytest.mark.asyncio
    async def test_scouting_create_basic(self, scouting_response: dict) -> None:
        route = respx.post(f"{BASE_URL}/v1/scouting/tasks").mock(
            return_value=httpx.Response(200, json=scouting_response)
        )

        client = YutoriClient(api_key="yut-test-key")
        try:
            result = await client.scouting_create("Monitor lu.ma for AI events")

            assert route.called
            import json
            body = json.loads(route.calls[0].request.content)
            assert body["task"] == "Monitor lu.ma for AI events"
            assert "start_url" not in body

            assert result.task_id == "scout-456"
            assert result.status == "scheduled"
        finally:
            await client.close()

    @respx.mock
    @pytest.mark.asyncio
    async def test_scouting_create_all_options(self, scouting_response: dict) -> None:
        route = respx.post(f"{BASE_URL}/v1/scouting/tasks").mock(
            return_value=httpx.Response(200, json=scouting_response)
        )

        client = YutoriClient(api_key="yut-test-key")
        try:
            await client.scouting_create(
                "Monitor lu.ma for AI events",
                start_url="https://lu.ma",
                schedule="0 9 * * *",
                webhook_url="https://nexus.dev/webhook",
            )

            import json
            body = json.loads(route.calls[0].request.content)
            assert body["start_url"] == "https://lu.ma"
            assert body["schedule"] == "0 9 * * *"
            assert body["webhook_url"] == "https://nexus.dev/webhook"
        finally:
            await client.close()
