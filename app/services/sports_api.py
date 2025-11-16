import httpx
from app.models.schemas import TeamInfo, MatchData
from fastapi import HTTPException
import logging


class TheSportsDBService:
    """Service for interacting with TheSportsDB API."""

    BASE_URL = "https://www.thesportsdb.com/api/v1/json/3"

    def __init__(self):
        self.client = httpx.AsyncClient(timeout=10.0)
        self.logger = logging.getLogger("sports-api")

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
            self.logger.info(f"Search team response for {team_name}: {data}")

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

    async def search_team_by_id(self, team_id: str) -> TeamInfo:
        """Search for a team by ID."""
        try:
            response = await self.client.get(
                f"{self.BASE_URL}/lookupteam.php", params={"id": team_id}
            )
            response.raise_for_status()
            data = response.json()
            self.logger.info(f"Search team by ID response for {team_id}: {data}")

            if not data.get("teams"):
                raise HTTPException(
                    status_code=404, detail=f"Team with ID '{team_id}' not found"
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

    async def get_recent_matches(self, team_id: str, limit: int = 10):
        """Fetch recent matches for a given team."""
        try:
            response = await self.client.get(
                f"{self.BASE_URL}/eventslast.php", params={"id": team_id}
            )
            response.raise_for_status()
            data = response.json()
            self.logger.info(f"API response for team_id {team_id}: {data}")

            matches = data.get("results", []) or []
            return matches[:limit]
        except httpx.HTTPError as e:
            raise HTTPException(
                status_code=500, detail=f"Error fetching recent matches: {str(e)}"
            )

    async def get_head_to_head(self, team1_id: str, team2_id: str, limit: int = 5):
        """Get last several matches between two teams."""
        response = await self.client.get(
            f"{self.BASE_URL}/eventslast.php", params={"id": team1_id}
        )
        response.raise_for_status()
        data = response.json()
        matches = data.get("results", []) or []

        # Debugging log to inspect the API response
        self.logger.info("API Response for head-to-head matches: %s", data)

        # Ensure matches is a list of dictionaries
        if not isinstance(matches, list) or not all(
            isinstance(m, dict) for m in matches
        ):
            self.logger.error("Unexpected data format for matches: %s", matches)
            raise ValueError("Invalid data format received from API")

        # Check for specific error messages in the API response
        if isinstance(data, dict) and data.get("results") == "Invalid Team ID passed":
            self.logger.error(
                "Invalid Team ID provided: team1_id=%s, team2_id=%s", team1_id, team2_id
            )
            raise ValueError("One or both team IDs are invalid.")

        result = []
        for m in matches:
            if m.get("idHomeTeam") == team2_id or m.get("idAwayTeam") == team2_id:
                result.append(m)
                if len(result) >= limit:
                    break

        return result
