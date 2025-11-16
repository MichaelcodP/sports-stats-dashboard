import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


class FakeFailingSportsAPI:
    """Fake sports API that raises exceptions."""

    async def search_team(self, team_name: str):
        raise Exception("API Error")

    async def search_team_by_id(self, team_id: str):
        raise Exception("API Error")

    async def get_recent_matches(self, team_id: str, limit: int = 5):
        raise Exception("API Error")

    async def get_head_to_head(self, team1_id: str, team2_id: str, limit: int = 5):
        raise Exception("API Error")

    async def get_match_between_teams(self, team1: str, team2: str):
        raise Exception("API Error")


class FakeFailingLLMService:
    """Fake LLM service that raises exceptions."""

    async def analyze_match(self, match):
        raise Exception("LLM Error")

    async def analyze_with_all_models(self, match):
        raise Exception("LLM Error")


@pytest.mark.asyncio
async def test_analyze_team_not_found(monkeypatch):
    """Test error handling when team is not found."""

    class FakeSportsAPI:
        async def search_team(self, team_name: str):
            from fastapi import HTTPException

            raise HTTPException(status_code=404, detail=f"Team '{team_name}' not found")

    monkeypatch.setattr("app.routes.analysis.sports_api", FakeSportsAPI())

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/analyze/team/NonExistentTeam")
        assert response.status_code == 404


@pytest.mark.asyncio
async def test_analyze_team_no_matches(monkeypatch):
    """Test error handling when team has no matches."""

    class FakeSportsAPI:
        async def search_team(self, team_name: str):
            from app.models.schemas import TeamInfo

            return TeamInfo(id="123", name=team_name, country="England")

        async def get_recent_matches(self, team_id: str, limit: int = 5):
            return []  # No matches

    monkeypatch.setattr("app.routes.analysis.sports_api", FakeSportsAPI())

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/analyze/team/Arsenal")
        assert response.status_code == 404
        assert "No matches found" in response.json()["detail"]


@pytest.mark.asyncio
async def test_analyze_match_api_error(monkeypatch):
    """Test error handling for API failures."""
    monkeypatch.setattr("app.routes.analysis.sports_api", FakeFailingSportsAPI())

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/analyze/vs/Arsenal/Chelsea")
        assert response.status_code == 500


@pytest.mark.asyncio
async def test_analyze_match_llm_error(monkeypatch):
    """Test error handling for LLM failures."""

    class FakeSportsAPI:
        async def get_match_between_teams(self, team1: str, team2: str):
            from app.models.schemas import MatchData

            return MatchData(
                event_id="test",
                home_team=team1,
                away_team=team2,
                home_score=1,
                away_score=0,
                date_event="2025-01-01",
            )

    monkeypatch.setattr("app.routes.analysis.sports_api", FakeSportsAPI())
    monkeypatch.setattr("app.routes.analysis.llm_service", FakeFailingLLMService())

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/analyze/vs/Arsenal/Chelsea")
        assert response.status_code == 500
