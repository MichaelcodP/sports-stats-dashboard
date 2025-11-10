from typing import Optional
from pydantic import BaseModel, Field


class TeamInfo(BaseModel):
    """Team information from TheSportsDB"""

    id: str
    name: str
    country: Optional[str] = None
    sport: Optional[str] = None
    league: Optional[str] = None


class MatchData(BaseModel):
    """Match data from TheSportsDB"""

    event_id: str = Field(..., description="Unique event ID")
    home_team: str = Field(..., description="Home team name")
    away_team: str = Field(..., description="Away team name")
    home_score: Optional[int] = Field(None, description="Home team score")
    away_score: Optional[int] = Field(None, description="Away team score")
    date_event: str = Field(..., description="Match date")
    stadium: Optional[str] = Field(None, description="Stadium name")
    league: Optional[str] = Field(None, description="League name")


class MatchAnalysis(BaseModel):
    """LLM-generated analysis of match data."""

    summary: str = Field(..., description="Brief match summary")
    key_insights: list[str] = Field(..., description="Key insights")
    performance_analysis: str = Field(..., description="Team performance analysis")
    prediction: Optional[str] = Field(None, description="Prediction for future matches")


class MatchAnalysisResponse(BaseModel):
    """Complete response with match data and analysis."""

    match_data: MatchData
    analysis: MatchAnalysis
