import pytest

from app.services.llm_service import LLMService
from app.models.schemas import MatchData, MatchAnalysis
from app.services.cache import InMemoryCache


class FakeProvider:
    """Simple fake provider that either returns text or raises an exception."""

    def __init__(self, name: str, text: str = None, exc: Exception = None):
        self.name = name
        self._text = text
        self._exc = exc

    async def generate(self, prompt: str) -> str:
        if self._exc:
            raise self._exc
        return self._text


@pytest.mark.asyncio
async def test_fallback_to_second_provider():
    # First provider raises, second returns valid JSON
    p1 = FakeProvider("p1", exc=Exception("simulated failure"))
    p2 = FakeProvider(
        "p2",
        text='{"summary":"OK","key_insights":[],"performance_analysis":"P","prediction":null}',
    )

    svc = LLMService(providers=[p1, p2], cache=InMemoryCache())

    match = MatchData(
        event_id="1",
        home_team="Team A",
        away_team="Team B",
        home_score=2,
        away_score=1,
        date_event="2025-01-01",
    )

    result = await svc.analyze_match(match)
    assert isinstance(result, MatchAnalysis)
    assert result.summary == "OK"
    assert result.performance_analysis == "P"


@pytest.mark.asyncio
async def test_all_providers_fail_raises():
    # All providers raise -> service should raise RuntimeError
    p1 = FakeProvider("p1", exc=Exception("first fail"))
    p2 = FakeProvider("p2", exc=Exception("second fail"))

    svc = LLMService(providers=[p1, p2])

    match = MatchData(
        event_id="2",
        home_team="X",
        away_team="Y",
        home_score=0,
        away_score=0,
        date_event="2025-01-02",
    )

    with pytest.raises(RuntimeError):
        await svc.analyze_match(match)
