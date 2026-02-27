from __future__ import annotations

import httpx
import pytest
import respx

from app.integrations.reka_client import RekaClient, RekaVisionResult

BASE_URL = "https://api.reka.ai"


# -- Fixtures ------------------------------------------------------------------


@pytest.fixture
def analyze_response() -> dict:
    return {
        "analysis": "This person appears to be interested in AI and startups.",
        "conversation_hooks": [
            "Recently visited Tokyo",
            "Attended Web Summit",
            "Interested in developer tools",
        ],
    }


@pytest.fixture
def compare_response() -> dict:
    return {
        "analysis": "The profile photos appear to be of the same person.",
        "conversation_hooks": [],
        "confidence": 0.92,
        "match": True,
    }


# -- Unit tests ----------------------------------------------------------------


class TestRekaVisionResult:
    def test_from_response_full(self, analyze_response: dict) -> None:
        result = RekaVisionResult.from_response(analyze_response)
        assert "AI and startups" in result.analysis
        assert len(result.conversation_hooks) == 3
        assert result.raw == analyze_response

    def test_from_response_missing_fields(self) -> None:
        result = RekaVisionResult.from_response({})
        assert result.analysis == ""
        assert result.conversation_hooks == []
        assert result.raw == {}

    def test_from_response_extra_fields(self, compare_response: dict) -> None:
        result = RekaVisionResult.from_response(compare_response)
        assert result.raw["confidence"] == 0.92
        assert result.raw["match"] is True


class TestRekaClientInit:
    def test_requires_api_key(self) -> None:
        with pytest.raises(ValueError, match="reka_api_key is required"):
            RekaClient(api_key="")


class TestRekaAnalyze:
    @respx.mock
    @pytest.mark.asyncio
    async def test_analyze_basic(self, analyze_response: dict) -> None:
        route = respx.post(f"{BASE_URL}/v1/vision/analyze").mock(
            return_value=httpx.Response(200, json=analyze_response)
        )

        client = RekaClient(api_key="reka-test-key")
        try:
            result = await client.analyze(
                url="https://instagram.com/sarahchen",
                prompt="Analyze this person's recent posts.",
            )

            assert route.called
            request = route.calls[0].request
            assert request.headers["X-API-Key"] == "reka-test-key"

            import json
            body = json.loads(request.content)
            assert body["url"] == "https://instagram.com/sarahchen"
            assert body["prompt"] == "Analyze this person's recent posts."

            assert "AI and startups" in result.analysis
            assert len(result.conversation_hooks) == 3
        finally:
            await client.close()

    @respx.mock
    @pytest.mark.asyncio
    async def test_analyze_server_error(self) -> None:
        respx.post(f"{BASE_URL}/v1/vision/analyze").mock(
            return_value=httpx.Response(500, json={"error": "internal"})
        )

        client = RekaClient(api_key="reka-test-key")
        try:
            with pytest.raises(httpx.HTTPStatusError):
                await client.analyze(
                    url="https://example.com/image.jpg",
                    prompt="Analyze this.",
                )
        finally:
            await client.close()

    @respx.mock
    @pytest.mark.asyncio
    async def test_analyze_auth_error(self) -> None:
        respx.post(f"{BASE_URL}/v1/vision/analyze").mock(
            return_value=httpx.Response(401, json={"error": "unauthorized"})
        )

        client = RekaClient(api_key="bad-key")
        try:
            with pytest.raises(httpx.HTTPStatusError):
                await client.analyze(url="https://example.com", prompt="test")
        finally:
            await client.close()


class TestRekaCompare:
    @respx.mock
    @pytest.mark.asyncio
    async def test_compare_basic(self, compare_response: dict) -> None:
        route = respx.post(f"{BASE_URL}/v1/vision/compare").mock(
            return_value=httpx.Response(200, json=compare_response)
        )

        client = RekaClient(api_key="reka-test-key")
        try:
            result = await client.compare(
                urls=[
                    "https://linkedin.com/photo/sarah.jpg",
                    "https://twitter.com/photo/sarah.jpg",
                ],
                prompt="Are these the same person?",
            )

            assert route.called
            import json
            body = json.loads(route.calls[0].request.content)
            assert len(body["urls"]) == 2
            assert body["prompt"] == "Are these the same person?"

            assert result.raw.get("match") is True
            assert result.raw.get("confidence") == 0.92
        finally:
            await client.close()

    @respx.mock
    @pytest.mark.asyncio
    async def test_compare_server_error(self) -> None:
        respx.post(f"{BASE_URL}/v1/vision/compare").mock(
            return_value=httpx.Response(503, json={"error": "unavailable"})
        )

        client = RekaClient(api_key="reka-test-key")
        try:
            with pytest.raises(httpx.HTTPStatusError):
                await client.compare(
                    urls=["https://a.jpg", "https://b.jpg"],
                    prompt="compare",
                )
        finally:
            await client.close()
