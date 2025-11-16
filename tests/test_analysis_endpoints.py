import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.models.schemas import MatchData, MatchAnalysis


class FakeLLMService:
    """Fake LLM service for testing."""

    async def analyze_match(self, match: MatchData):
        return MatchAnalysis(
            summary="Test analysis",
            key_insights=["Test insight"],
            performance_analysis="Test performance",
            prediction="Test prediction",
        )

    async def analyze_with_all_models(self, match: MatchData):
        analysis = MatchAnalysis(
            summary="Test analysis",
            key_insights=["Test insight"],
            performance_analysis="Test performance",
            prediction="Test prediction",
        )
        return {"openai": analysis, "gemini": analysis, "groq": analysis}


class FakeSportsAPI:
    """Fake sports API for testing."""

    async def search_team(self, team_name: str):
        from app.models.schemas import TeamInfo

        return TeamInfo(id="123", name=team_name, country="England")

    async def search_team_by_id(self, team_id: str):
        from app.models.schemas import TeamInfo

        return TeamInfo(id=team_id, name="Test Team", country="England")

    async def get_recent_matches(self, team_id: str, limit: int = 5):
        return [
            {
                "idEvent": f"event_{i}",
                "strHomeTeam": "Test Team" if i % 2 == 0 else "Opponent",
                "strAwayTeam": "Opponent" if i % 2 == 0 else "Test Team",
                "intHomeScore": 2,
                "intAwayScore": 1,
                "dateEvent": "2025-01-01",
                "strVenue": "Test Stadium",
                "strLeague": "Test League",
            }
            for i in range(min(limit, 3))
        ]

    async def get_head_to_head(self, team1_id: str, team2_id: str, limit: int = 5):
        return [
            {
                "idEvent": f"h2h_{i}",
                "strHomeTeam": "Team1" if i % 2 == 0 else "Team2",
                "strAwayTeam": "Team2" if i % 2 == 0 else "Team1",
                "intHomeScore": 2,
                "intAwayScore": 1,
                "dateEvent": "2025-01-01",
                "strVenue": "Test Stadium",
                "strLeague": "Test League",
            }
            for i in range(min(limit, 2))
        ]

    async def get_match_between_teams(self, team1: str, team2: str):
        return MatchData(
            event_id="test_event",
            home_team=team1,
            away_team=team2,
            home_score=2,
            away_score=1,
            date_event="2025-01-01",
            stadium="Test Stadium",
            league="Test League",
        )


@pytest.mark.asyncio
async def test_analyze_match_endpoint(monkeypatch):
    """Test the /api/analyze/vs/{team1}/{team2} endpoint."""
    # Mock dependencies
    monkeypatch.setattr("app.routes.analysis.llm_service", FakeLLMService())
    monkeypatch.setattr("app.routes.analysis.sports_api", FakeSportsAPI())

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/analyze/vs/Arsenal/Chelsea")
        assert response.status_code == 200

        data = response.json()
        assert "teams" in data
        assert "date" in data
        assert "stadium" in data
        assert "llm_analysis" in data
        assert data["teams"] == "Arsenal vs Chelsea"


@pytest.mark.asyncio
async def test_analyze_team_by_name_endpoint(monkeypatch):
    """Test the /api/analyze/team/{team_name} endpoint."""
    monkeypatch.setattr("app.routes.analysis.llm_service", FakeLLMService())
    monkeypatch.setattr("app.routes.analysis.sports_api", FakeSportsAPI())

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/analyze/team/Arsenal")
        assert response.status_code == 200

        data = response.json()
        assert data["team_name"] == "Arsenal"
        assert data["team_id"] == "123"
        assert "matches" in data
        assert len(data["matches"]) == 3  # Limited by our fake data

        # Check structure of each match
        for match_data in data["matches"]:
            assert "match" in match_data
            assert "analysis" in match_data


@pytest.mark.asyncio
async def test_analyze_team_by_id_endpoint(monkeypatch):
    """Test the /api/analyze/team/id/{team_id} endpoint."""
    monkeypatch.setattr("app.routes.analysis.llm_service", FakeLLMService())
    monkeypatch.setattr("app.routes.analysis.sports_api", FakeSportsAPI())

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/analyze/team/id/123")
        assert response.status_code == 200

        data = response.json()
        assert data["team_id"] == "123"
        assert data["team_name"] == "Test Team"
        assert "matches" in data
        assert len(data["matches"]) == 3


@pytest.mark.asyncio
async def test_analyze_head_to_head_endpoint(monkeypatch):
    """Test the /api/analyze/h2h/{team1_name}/{team2_name} endpoint."""
    monkeypatch.setattr("app.routes.analysis.llm_service", FakeLLMService())
    monkeypatch.setattr("app.routes.analysis.sports_api", FakeSportsAPI())

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/analyze/h2h/Arsenal/Chelsea")
        assert response.status_code == 200

        data = response.json()
        assert data["team1"] == "Arsenal"
        assert data["team2"] == "Chelsea"
        assert "matches" in data
        assert len(data["matches"]) == 2


@pytest.mark.asyncio
async def test_analyze_all_models_endpoint(monkeypatch):
    """Test the /api/analyze/all-models/{team1}/{team2} endpoint."""
    monkeypatch.setattr("app.routes.analysis.llm_service", FakeLLMService())
    monkeypatch.setattr("app.routes.analysis.sports_api", FakeSportsAPI())

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/analyze/all-models/Arsenal/Chelsea")
        assert response.status_code == 200

        data = response.json()
        assert "teams" in data
        assert "event_id" in data
        assert "models" in data
        assert "openai" in data["models"]
        assert "gemini" in data["models"]
        assert "groq" in data["models"]
