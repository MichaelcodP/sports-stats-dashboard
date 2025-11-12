from app.services.sports_api import TheSportsDBService
from app.services.llm_service import LLMService
from fastapi import APIRouter, HTTPException


router = APIRouter()

sports_api = TheSportsDBService()
llm_service = LLMService()


@router.get("/analyze/{team1}/{team2}")
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
            "llm_analysis": analysis.dict(),
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
