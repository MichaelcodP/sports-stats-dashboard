import pytest
from httpx import AsyncClient
from httpx import ASGITransport
from app.main import app


@pytest.mark.asyncio
async def test_health_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/api/health")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert "uptime_seconds" in payload
    assert "components" in payload
    assert payload["components"]["llm_service"]["ok"] is True
    assert payload["components"]["sports_api"]["ok"] is True
