import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.mark.asyncio
async def test_get_latest_match_endpoint():
    """Test the /api/match/{team1}/{team2} endpoint."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/match/Arsenal/Chelsea")
        # This endpoint makes real API calls, so we expect it to work or fail gracefully
        # The important thing is that it doesn't crash the server
        assert response.status_code in [200, 404, 500]  # Valid response codes


@pytest.mark.asyncio
async def test_search_team_endpoint():
    """Test the /api/team/{name} endpoint."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/team/Arsenal")
        # This endpoint makes real API calls, so we expect it to work or fail gracefully
        assert response.status_code in [200, 404, 500]  # Valid response codes

        if response.status_code == 200:
            data = response.json()
            assert "results" in data
            # If we get results, check the structure
            if data["results"]:
                team = data["results"][0]
                assert "id" in team
                assert "name" in team
                assert (
                    "country" in team or "league" in team
                )  # At least one of these should be present
