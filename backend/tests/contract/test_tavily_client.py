from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from app.integrations.tavily_client import TavilyClient, TavilySearchResult


# -- Fixtures ------------------------------------------------------------------

@pytest.fixture
def tavily_response() -> dict:
    return {
        "query": "AI events in SF",
        "answer": "Several AI events are happening in SF this week.",
        "results": [
            {
                "title": "AI Founders Dinner",
                "url": "https://lu.ma/ai-dinner-sf",
                "content": "Intimate gathering of 30 founders.",
                "score": 0.95,
                "raw_content": "# AI Founders Dinner\nFull markdown content here.",
            },
            {
                "title": "DevTools Meetup",
                "url": "https://meetup.com/devtools-sf",
                "content": "Monthly devtools meetup.",
                "score": 0.82,
                "raw_content": None,
            },
        ],
    }


# -- Unit tests ----------------------------------------------------------------


class TestTavilySearchResult:
    def test_from_response_full(self, tavily_response: dict) -> None:
        result = TavilySearchResult.from_response(tavily_response)
        assert result.query == "AI events in SF"
        assert result.answer == "Several AI events are happening in SF this week."
        assert len(result.results) == 2
        assert result.results[0]["url"] == "https://lu.ma/ai-dinner-sf"
        # raw_content skips None entries
        assert len(result.raw_content) == 1
        assert "AI Founders Dinner" in result.raw_content[0]

    def test_from_response_missing_fields(self) -> None:
        result = TavilySearchResult.from_response({})
        assert result.query == ""
        assert result.answer is None
        assert result.results == []
        assert result.raw_content == []

    def test_from_response_no_answer(self, tavily_response: dict) -> None:
        tavily_response.pop("answer")
        result = TavilySearchResult.from_response(tavily_response)
        assert result.answer is None


class TestTavilyClientInit:
    def test_requires_api_key(self) -> None:
        with pytest.raises(ValueError, match="tavily_api_key is required"):
            TavilyClient(api_key="")


class TestTavilyClientSearch:
    @pytest.mark.asyncio
    async def test_search_basic(self, tavily_response: dict) -> None:
        with patch(
            "app.integrations.tavily_client.AsyncTavilyClient"
        ) as MockClient:
            mock_instance = MockClient.return_value
            mock_instance.search = AsyncMock(return_value=tavily_response)

            client = TavilyClient(api_key="tvly-test-key")
            result = await client.search("AI events in SF")

            mock_instance.search.assert_called_once_with(
                query="AI events in SF",
                search_depth="advanced",
                max_results=10,
                include_answer=False,
                include_raw_content=False,
            )
            assert result.query == "AI events in SF"
            assert result.answer is not None

    @pytest.mark.asyncio
    async def test_search_with_all_options(self, tavily_response: dict) -> None:
        with patch(
            "app.integrations.tavily_client.AsyncTavilyClient"
        ) as MockClient:
            mock_instance = MockClient.return_value
            mock_instance.search = AsyncMock(return_value=tavily_response)

            client = TavilyClient(api_key="tvly-test-key")
            result = await client.search(
                "AI events",
                search_depth="basic",
                max_results=5,
                include_domains=["lu.ma", "meetup.com"],
                time_range="week",
                include_answer=True,
                include_raw_content=True,
            )

            mock_instance.search.assert_called_once_with(
                query="AI events",
                search_depth="basic",
                max_results=5,
                include_answer=True,
                include_raw_content=True,
                include_domains=["lu.ma", "meetup.com"],
                days=7,
            )
            assert isinstance(result, TavilySearchResult)

    @pytest.mark.asyncio
    async def test_search_time_range_day(self, tavily_response: dict) -> None:
        with patch(
            "app.integrations.tavily_client.AsyncTavilyClient"
        ) as MockClient:
            mock_instance = MockClient.return_value
            mock_instance.search = AsyncMock(return_value=tavily_response)

            client = TavilyClient(api_key="tvly-test-key")
            await client.search("news", time_range="day")

            call_kwargs = mock_instance.search.call_args.kwargs
            assert call_kwargs["days"] == 1

    @pytest.mark.asyncio
    async def test_search_error_propagates(self) -> None:
        with patch(
            "app.integrations.tavily_client.AsyncTavilyClient"
        ) as MockClient:
            mock_instance = MockClient.return_value
            mock_instance.search = AsyncMock(
                side_effect=Exception("API rate limit exceeded")
            )

            client = TavilyClient(api_key="tvly-test-key")
            with pytest.raises(Exception, match="API rate limit exceeded"):
                await client.search("test")
