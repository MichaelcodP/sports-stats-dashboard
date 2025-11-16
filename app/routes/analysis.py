from app.services.sports_api import TheSportsDBService
from app.services.llm_service import LLMService
from fastapi import APIRouter, HTTPException
from app.models import MatchData
import logging


router = APIRouter()

sports_api = TheSportsDBService()
llm_service = LLMService()

logger = logging.getLogger(__name__)


@router.get("/analyze/team/{team_name}")
async def analyze_team_last_matches_by_name(team_name: str):
    """Analyze last 5 matches of a team."""
    logger.info(f"Endpoint called with team_name: {team_name}")
    try:
        team = await sports_api.search_team(team_name)
        matches = await sports_api.get_recent_matches(team.id, limit=5)
        if not matches:
            raise HTTPException(status_code=404, detail="No matches found")

        match_list = []
        analyses = []
        for m in matches:
            match_data = MatchData(
                event_id=m["idEvent"],
                home_team=m["strHomeTeam"],
                away_team=m["strAwayTeam"],
                home_score=int(m["intHomeScore"]) if m.get("intHomeScore") else None,
                away_score=int(m["intAwayScore"]) if m.get("intAwayScore") else None,
                date_event=m["dateEvent"],
                stadium=m.get("strVenue"),
                league=m.get("strLeague"),
            )

            analysis = await llm_service.analyze_match(match_data)
            match_list.append(
                {
                    "home_team": match_data.home_team,
                    "away_team": match_data.away_team,
                    "home_score": match_data.home_score,
                    "away_score": match_data.away_score,
                    "date": match_data.date_event,
                    "league": match_data.league,
                }
            )
            analyses.append(analysis)

        # Combine analyses into one
        overall_analysis = "\n\n".join(
            [
                f"Match: {m['strHomeTeam']} vs {m['strAwayTeam']}\n"
                f"Summary: {a.summary}\n"
                f"Key Insights: {', '.join(a.key_insights)}\n"
                f"Performance Analysis: {a.performance_analysis}\n"
                f"Prediction: {a.prediction or 'N/A'}"
                for m, a in zip(matches, analyses)
            ]
        )

        return {
            "team_name": team.name,
            "country": team.country,
            "sport": team.sport,
            "league": team.league,
            "matches": match_list,
            "analysis": overall_analysis,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analyze/team/id/{team_id}")
async def analyze_team_last_matches(team_id: str):
    """Analyze last 5 matches of a team."""
    logger.info(f"Endpoint called with team_id: {team_id}")
    try:
        team = await sports_api.search_team_by_id(team_id)
        matches = await sports_api.get_recent_matches(team_id, limit=5)
        if not matches:
            raise HTTPException(status_code=404, detail="No matches found")

        analyses = []
        for m in matches:
            match_data = MatchData(
                event_id=m["idEvent"],
                home_team=m["strHomeTeam"],
                away_team=m["strAwayTeam"],
                home_score=int(m["intHomeScore"]) if m.get("intHomeScore") else None,
                away_score=int(m["intAwayScore"]) if m.get("intAwayScore") else None,
                date_event=m["dateEvent"],
                stadium=m.get("strVenue"),
                league=m.get("strLeague"),
            )

            analysis = await llm_service.analyze_match(match_data)
            analyses.append({"match": match_data, "analysis": analysis})

        return {
            "team_id": team_id,
            "team_name": team.name if hasattr(team, "name") else None,
            "matches": analyses,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analyze/h2h/{team1_name}/{team2_name}")
async def analyze_head_to_head(team1_name: str, team2_name: str):
    """Analyze recent head-to-head matches between two teams."""
    try:
        team1 = await sports_api.search_team(team1_name)
        team2 = await sports_api.search_team(team2_name)
        h2h_matches = await sports_api.get_head_to_head(team1.id, team2.id, limit=5)

        if not h2h_matches:
            raise HTTPException(status_code=404, detail="No H2H matches found")

        results = []
        for m in h2h_matches:
            match_data = MatchData(
                event_id=m["idEvent"],
                home_team=m["strHomeTeam"],
                away_team=m["strAwayTeam"],
                home_score=int(m["intHomeScore"]) if m.get("intHomeScore") else None,
                away_score=int(m["intAwayScore"]) if m.get("intAwayScore") else None,
                date_event=m["dateEvent"],
                stadium=m.get("strVenue"),
                league=m.get("strLeague"),
            )

            analysis = await llm_service.analyze_match(match_data)
            results.append({"match": match_data, "analysis": analysis})

        return {"team1": team1_name, "team2": team2_name, "matches": results}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analyze/all-models/{team1}/{team2}")
async def analyze_all_models(team1: str, team2: str):
    """Return analysis from ALL LLM providers."""
    try:
        match_data = await sports_api.get_match_between_teams(team1, team2)
        if not match_data:
            raise HTTPException(404, "No match data found")

        results = await llm_service.analyze_with_all_models(match_data)

        return {
            "teams": f"{match_data.home_team} vs {match_data.away_team}",
            "event_id": match_data.event_id,
            "models": {
                name: res.model_dump() if res else None for name, res in results.items()
            },
        }

    except Exception as e:
        raise HTTPException(500, detail=str(e))


@router.get("/analyze/vs/{team1}/{team2}")
async def analyze_match(team1: str, team2: str):
    """Analyze the latest match between two teams using LLM."""
    try:
        match_data = await sports_api.get_match_between_teams(team1, team2)
        if not match_data:
            raise HTTPException(status_code=404, detail="No match data found")

        analysis = await llm_service.analyze_match(match_data)

        return {
            "teams": f"{match_data.home_team} vs {match_data.away_team}",
            "date": match_data.date_event,
            "stadium": match_data.stadium,
            "llm_analysis": analysis.model_dump(),
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analyze/{team1}/{team2}")
async def analyze_match_compat(team1: str, team2: str):
    """Compatibility route used in tests."""
    return await analyze_match(team1, team2)
