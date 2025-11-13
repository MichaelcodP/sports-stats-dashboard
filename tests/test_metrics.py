from fastapi.testclient import TestClient
from app.main import app
from app.data_store import match_store

client = TestClient(app)

def setup_module(module):
    """Setup test data in the MatchStore."""
    match_store.update_matches([
        {
            "strHomeTeam": "Arsenal",
            "strAwayTeam": "Chelsea",
            "intHomeScore": 2,
            "intAwayScore": 1,
        },
        {
            "strHomeTeam": "Liverpool",
            "strAwayTeam": "Arsenal",
            "intHomeScore": 3,
            "intAwayScore": 3,
        },
        {
            "strHomeTeam": "Chelsea",
            "strAwayTeam": "Liverpool",
            "intHomeScore": 0,
            "intAwayScore": 2,
        },
    ])

def teardown_module(module):
    """Clear the MatchStore after tests."""
    match_store.update_matches([])

def test_metrics_for_team():
    response = client.get("/api/metrics/Arsenal")
    assert response.status_code == 200
    data = response.json()
    assert data["team"] == "Arsenal"
    assert data["matches_analyzed"] == 2
    assert round(data["avg_goals"], 2) == 2.5
    assert round(data["avg_conceded"], 2) == 2.0
    assert round(data["win_rate_percent"], 1) == 50.0
    assert round(data["form_score_last_5"], 2) == 2.0
    assert round(data["xG"], 2) == 2.75
    assert round(data["attack_efficiency"], 2) == 0.83
    assert round(data["defense_efficiency"], 2) == 0.33

def test_metrics_with_opponent_filter():
    response = client.get("/api/metrics/Arsenal?opponent=Chelsea")
    assert response.status_code == 200
    data = response.json()
    assert data["team"] == "Arsenal"
    assert data["matches_analyzed"] == 1
    assert round(data["avg_goals"], 2) == 2
    assert round(data["avg_conceded"], 2) == 1
    assert round(data["win_rate_percent"], 1) == 100.0
    assert round(data["form_score_last_5"], 2) == 3.0
    assert round(data["xG"], 2) == 2.2
    assert round(data["attack_efficiency"], 2) == 0.67
    assert round(data["defense_efficiency"], 2) == 0.67

def test_metrics_with_no_matches():
    response = client.get("/api/metrics/Manchester United")
    assert response.status_code == 404
    assert response.json()["detail"] == "No matches found for this team"
