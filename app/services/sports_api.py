import httpx
from app.models.schemas import TeamInfo, MatchData
from fastapi import HTTPException


class TheSportsDBService:
    """Service for interacting with TheSportsDB API."""

    BASE_URL = "https://www.thesportsdb.com/api/v1/json/3"

    def __init__(self):
        self.client = httpx.AsyncClient(timeout=10.0)

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()

    async def search_team(self, team_name: str) -> TeamInfo:
        """Search for a team by name."""
        try:
            response = await self.client.get(
                f"{self.BASE_URL}/searchteams.php", params={"t": team_name}
            )
            response.raise_for_status()
            data = response.json()

            if not data.get("teams"):
                raise HTTPException(
                    status_code=404, detail=f"Team '{team_name}' not found"
                )

            team = data["teams"][0]
            return TeamInfo(
                id=team["idTeam"],
                name=team["strTeam"],
                country=team.get("strCountry"),
                sport=team.get("strSport"),
                league=team.get("strLeague"),
            )

        except httpx.HTTPError as e:
            raise HTTPException(
                status_code=500, detail=f"Error fetching team: {str(e)}"
            )

    async def get_latest_events(self, team_id: str) -> list:
        """Get latest events for a team."""
        try:
            response = await self.client.get(
                f"{self.BASE_URL}/eventslast.php", params={"id": team_id}
            )
            response.raise_for_status()
            data = response.json()
            return data.get("results", []) or []

        except httpx.HTTPError as e:
            raise HTTPException(
                status_code=500, detail=f"Error fetching events: {str(e)}"
            )

    async def get_next_events(self, team_id: str) -> list:
        """Get upcoming events for a team."""
        try:
            response = await self.client.get(
                f"{self.BASE_URL}/eventsnext.php", params={"id": team_id}
            )
            response.raise_for_status()
            data = response.json()
            return data.get("events", []) or []

        except httpx.HTTPError as e:
            raise HTTPException(
                status_code=500, detail=f"Error fetching events: {str(e)}"
            )

    async def get_match_between_teams(
        self, team1_name: str, team2_name: str
    ) -> MatchData:
        """Get the latest match between two teams."""
        # Search for both teams
        team1 = await self.search_team(team1_name)
        team2 = await self.search_team(team2_name)

        # Get latest events for team1
        last_events = await self.get_latest_events(team1.id)

        # Find match between these teams
        latest_match = None
        for event in last_events:
            if (
                event.get("idHomeTeam") == team2.id
                or event.get("idAwayTeam") == team2.id
            ):
                latest_match = event
                break

        # If no match found, try next events
        if not latest_match:
            next_events = await self.get_next_events(team1.id)
            for event in next_events:
                if (
                    event.get("idHomeTeam") == team2.id
                    or event.get("idAwayTeam") == team2.id
                ):
                    latest_match = event
                    break

        if not latest_match:
            raise HTTPException(
                status_code=404,
                detail=f"No matches between {team1_name} and {team2_name}",
            )

        # Return as Pydantic model
        return MatchData(
            event_id=latest_match["idEvent"],
            home_team=latest_match["strHomeTeam"],
            away_team=latest_match["strAwayTeam"],
            home_score=(
                int(latest_match["intHomeScore"])
                if latest_match.get("intHomeScore")
                else None
            ),
            away_score=(
                int(latest_match["intAwayScore"])
                if latest_match.get("intAwayScore")
                else None
            ),
            date_event=latest_match["dateEvent"],
            stadium=latest_match.get("strVenue"),
            league=latest_match.get("strLeague"),
        )
