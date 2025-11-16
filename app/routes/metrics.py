from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from app.data_store import match_store

router = APIRouter()


@router.get("/metrics")
def get_system_metrics():
    """
    Get overall system metrics.
    """
    matches = match_store.get_all()

    if not matches:
        return {
            "total_matches": 0,
            "total_teams": 0,
            "avg_goals_per_match": 0,
            "total_goals": 0,
        }

    total_matches = len(matches)
    teams = set()
    total_goals = 0

    for match in matches:
        teams.add(match.get("strHomeTeam", ""))
        teams.add(match.get("strAwayTeam", ""))
        home_goals = int(match.get("intHomeScore") or 0)
        away_goals = int(match.get("intAwayScore") or 0)
        total_goals += home_goals + away_goals

    return {
        "total_matches": total_matches,
        "total_teams": len(teams),
        "avg_goals_per_match": (
            round(total_goals / total_matches, 2) if total_matches > 0 else 0
        ),
        "total_goals": total_goals,
    }


@router.get("/metrics/{team_name}")
def get_team_metrics(
    team_name: str,
    opponent: Optional[str] = Query(None),
    match_type: Optional[str] = Query(None),
    last_n: int = 5,
):
    """
    Get metrics for a team.
    - opponent: optional, filter by opponent team
    - match_type: optional, 'home' or 'away'
    - last_n: number of recent matches to calculate form score
    """
    matches = match_store.get_all()

    # Filter matches by team
    team_matches = [
        m
        for m in matches
        if m.get("strHomeTeam", "").lower() == team_name.lower()
        or m.get("strAwayTeam", "").lower() == team_name.lower()
    ]

    if not team_matches:
        raise HTTPException(status_code=404, detail="No matches found for this team")

    # Filter by opponent
    if opponent:
        team_matches = [
            m
            for m in team_matches
            if m.get("strHomeTeam", "").lower() == opponent.lower()
            or m.get("strAwayTeam", "").lower() == opponent.lower()
        ]

    # Filter by match type
    if match_type:
        if match_type.lower() == "home":
            team_matches = [
                m
                for m in team_matches
                if m.get("strHomeTeam", "").lower() == team_name.lower()
            ]
        elif match_type.lower() == "away":
            team_matches = [
                m
                for m in team_matches
                if m.get("strAwayTeam", "").lower() == team_name.lower()
            ]

    if not team_matches:
        raise HTTPException(
            status_code=404, detail="No matches found with the specified filters"
        )

    # Metrics calculation
    total_goals = 0
    total_conceded = 0
    wins = 0
    recent_results = []

    for match in team_matches:
        home = match["strHomeTeam"]
        home_goals = int(match.get("intHomeScore") or 0)
        away_goals = int(match.get("intAwayScore") or 0)

        if team_name.lower() == home.lower():
            goals = home_goals
            conceded = away_goals
        else:
            goals = away_goals
            conceded = home_goals

        total_goals += goals
        total_conceded += conceded

        if goals > conceded:
            wins += 1
            recent_results.append(3)
        elif goals == conceded:
            recent_results.append(1)
        else:
            recent_results.append(0)

    total_matches = len(team_matches)
    avg_goals = total_goals / total_matches
    avg_conceded = total_conceded / total_matches
    win_rate = wins / total_matches * 100
    form_score = sum(recent_results[-last_n:]) / min(last_n, len(recent_results))

    xG = avg_goals * 1.1

    attack_efficiency = min(1.0, avg_goals / 3)
    defense_efficiency = max(0.0, 1 - avg_conceded / 3)

    return {
        "team": team_name,
        "matches_analyzed": total_matches,
        "avg_goals": round(avg_goals, 2),
        "avg_conceded": round(avg_conceded, 2),
        "win_rate_percent": round(win_rate, 1),
        "form_score_last_5": round(form_score, 2),
        "xG": round(xG, 2),
        "attack_efficiency": round(attack_efficiency, 2),
        "defense_efficiency": round(defense_efficiency, 2),
    }
