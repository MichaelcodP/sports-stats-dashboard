import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.models.schemas import MatchData, MatchAnalysis


# A fake LLM provider that returns canned JSON
class FakeProvider:
    def __init__(self, text=None):
        self.name = "fake"
        self._text = text or (
            '{"summary":"Demo analysis.","key_insights":["Insight A","Insight B"],'
            '"performance_analysis":"Demo performance","prediction":null}'
        )

    async def generate(self, prompt: str) -> str:
        return self._text


# A fake provider container
class FakeLLMService:
    def __init__(self, provider_text=None):
        self.providers = [FakeProvider(text=provider_text)]

    async def analyze_match(self, match: MatchData):
        # Return a MatchAnalysis model so the route can call .dict()
        return MatchAnalysis(
            summary="Demo analysis.",
            key_insights=["Insight A", "Insight B"],
            performance_analysis="Demo performance",
            prediction=None,
        )


# Fake sports API function
async def fake_get_match_between_teams(team1: str, team2: str):
    return MatchData(
        event_id="evt-1",
        home_team=team1,
        away_team=team2,
        home_score=2,
        away_score=1,
        date_event="2025-01-01",
        stadium="Demo Stadium",
        league="Demo League",
    )


@pytest.mark.asyncio
async def test_analyze_endpoint_monkeypatched(monkeypatch):

    # 1) Replace the sports_api.get_match_between_teams function used by the route
    monkeypatch.setattr(
        "app.routes.analysis.sports_api.get_match_between_teams",
        fake_get_match_between_teams,
        raising=False,
    )

    # 2) Replace the module-level llm_service instance with our fake service instance
    monkeypatch.setattr(
        "app.routes.analysis.llm_service",
        FakeLLMService(),
        raising=False,
    )

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/analyze/Arsenal/Brighton%20and%20Hove%20Albion")
        assert resp.status_code == 200, resp.text
        data = resp.json()
        # Basic assertions on the structure you return in the route
        assert data["teams"].startswith("Arsenal vs")
        assert data["date"] == "2025-01-01"
        assert "llm_analysis" in data
        # The fake LLM returns a dict; verify keys exist
        assert data["llm_analysis"]["summary"].startswith("Demo")
