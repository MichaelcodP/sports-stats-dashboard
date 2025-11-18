import httpx
from app.models.schemas import TeamInfo, MatchData
from fastapi import HTTPException
import logging
import os
from .mock_data import MockSportsData


class TheSportsDBService:
    """Service for interacting with TheSportsDB API."""

    BASE_URL = "https://www.thesportsdb.com/api/v1/json/3"

    def __init__(self):
        self.client = httpx.AsyncClient(timeout=10.0)
        self.logger = logging.getLogger("sports-api")
        self.api_key = os.getenv("THESPORTSDB_API_KEY")

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()

    async def search_team(self, team_name: str) -> TeamInfo:
        """Search for a team by name."""
        try:
            params = {"t": team_name}
            if self.api_key:
                params["APIkey"] = self.api_key

            response = await self.client.get(
                f"{self.BASE_URL}/searchteams.php", params=params
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
            error_msg = f"Error fetching team: {str(e)}"
            if "cloudflare" in str(e).lower() or "500" in str(e):
                self.logger.warning("TheSportsDB API unavailable, using mock data")
                return MockSportsData.get_mock_team(team_name)
            raise HTTPException(status_code=500, detail=error_msg)

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
            error_msg = f"Error fetching events: {str(e)}"
            if "cloudflare" in str(e).lower() or "500" in str(e):
                self.logger.warning(
                    "TheSportsDB API unavailable, using mock events data"
                )
                return self._get_mock_events(team_id, "last")
            raise HTTPException(status_code=500, detail=error_msg)

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
            error_msg = f"Error fetching events: {str(e)}"
            if "cloudflare" in str(e).lower() or "500" in str(e):
                self.logger.warning(
                    "TheSportsDB API unavailable, using mock events data"
                )
                return self._get_mock_events(team_id, "next")
            raise HTTPException(status_code=500, detail=error_msg)

    async def get_match_between_teams(
        self, team1_name: str, team2_name: str
    ) -> MatchData:
        """Get the latest match between two teams."""
        try:
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
                self.logger.warning(
                    f"No matches found between {team1_name} and {team2_name}, using mock data"
                )
                return self._get_mock_match_between_teams(team1_name, team2_name)

            # Return as Pydantic model
            return MatchData(
                event_id=latest_match["idEvent"],
                home_team=latest_match["strHomeTeam"],
                away_team=latest_match["strAwayTeam"],
                home_score=(
                    int(latest_match["intHomeScore"])
                    if latest_match.get("intHomeScore") is not None
                    else None
                ),
                away_score=(
                    int(latest_match["intAwayScore"])
                    if latest_match.get("intAwayScore") is not None
                    else None
                ),
                date_event=latest_match["dateEvent"],
                stadium=latest_match.get("strVenue"),
                league=latest_match.get("strLeague"),
            )
        except httpx.HTTPError as e:
            error_msg = f"Error fetching match data: {str(e)}"
            if "cloudflare" in str(e).lower() or "500" in str(e):
                self.logger.warning(
                    "TheSportsDB API unavailable, using mock data for match"
                )
                return self._get_mock_match_between_teams(team1_name, team2_name)
            raise HTTPException(status_code=500, detail=error_msg)

    def _get_mock_match_between_teams(
        self, team1_name: str, team2_name: str
    ) -> MatchData:
        """Create mock match data between two teams."""
        import random
        from datetime import datetime

        # Randomly decide which team is home
        is_team1_home = random.choice([True, False])
        home_team = team1_name if is_team1_home else team2_name
        away_team = team2_name if is_team1_home else team1_name

        # Random scores
        home_score = random.randint(0, 4)
        away_score = random.randint(0, 4)

        return MatchData(
            event_id=f"mock_{team1_name}_{team2_name}",
            home_team=home_team,
            away_team=away_team,
            home_score=home_score,
            away_score=away_score,
            date_event=datetime.now().strftime("%Y-%m-%d"),
            stadium=f"{home_team} Stadium",
            league="Premier League",
        )

    def _get_mock_events(self, team_id: str, event_type: str) -> list:
        """Create mock events data for a team."""
        import random
        from datetime import datetime, timedelta

        # Get team name from ID
        team_name = "Arsenal"  # Default
        for team_data in MockSportsData.MOCK_TEAMS.values():
            if team_data["id"] == team_id:
                team_name = team_data["name"]
                break

        # Create a few mock events
        events = []
        premier_league_teams = [
            "Arsenal",
            "Chelsea",
            "Liverpool",
            "Manchester United",
            "Manchester City",
            "Tottenham",
            "Newcastle",
            "Brighton",
            "Fulham",
            "Crystal Palace",
        ]

        # Remove current team
        available_opponents = [t for t in premier_league_teams if t != team_name]

        for i in range(3):
            # For "last" events, use past dates; for "next" events, use future dates
            if event_type == "last":
                event_date = datetime.now() - timedelta(days=(i + 1) * 7)
            else:
                event_date = datetime.now() + timedelta(days=(i + 1) * 7)

            opponent = random.choice(available_opponents)
            is_home = random.choice([True, False])

            event = {
                "idEvent": f"mock_event_{team_id}_{i}",
                "idHomeTeam": team_id if is_home else f"mock_{opponent}_id",
                "idAwayTeam": f"mock_{opponent}_id" if is_home else team_id,
                "strHomeTeam": team_name if is_home else opponent,
                "strAwayTeam": opponent if is_home else team_name,
                "intHomeScore": random.randint(0, 4) if event_type == "last" else None,
                "intAwayScore": random.randint(0, 4) if event_type == "last" else None,
                "dateEvent": event_date.strftime("%Y-%m-%d"),
                "strVenue": (
                    f"{team_name} Stadium" if is_home else f"{opponent} Stadium"
                ),
                "strLeague": "Premier League",
            }
            events.append(event)

        return events

    async def get_recent_matches(self, team_id: str, limit: int = 10):
        """Fetch recent matches for a given team."""
        try:
            params = {"id": team_id}
            if self.api_key:
                params["APIkey"] = self.api_key

            response = await self.client.get(
                f"{self.BASE_URL}/eventslast.php", params=params
            )
            response.raise_for_status()
            data = response.json()
            self.logger.info(f"API response for team_id {team_id}: {data}")

            matches = data.get("results", []) or []
            if len(matches) < limit:
                self.logger.warning(
                    f"API returned only {len(matches)} matches, supplementing with mock data"
                )
                mock_matches = MockSportsData.get_mock_matches(
                    team_id, limit - len(matches)
                )
                matches.extend(mock_matches)
            return matches[:limit]
        except httpx.HTTPError as e:
            error_msg = f"Error fetching recent matches: {str(e)}"
            if "cloudflare" in str(e).lower() or "500" in str(e):
                self.logger.warning("TheSportsDB API unavailable, using mock data")
                return MockSportsData.get_mock_matches(team_id, limit)
            raise HTTPException(status_code=500, detail=error_msg)

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

    async def get_match_by_id(self, match_id: str) -> MatchData:
        """Get match data by event ID."""
        try:
            response = await self.client.get(
                f"{self.BASE_URL}/lookupevent.php", params={"id": match_id}
            )
            response.raise_for_status()
            data = response.json()
            self.logger.info(f"Lookup event response for {match_id}: {data}")

            if not data.get("events"):
                raise HTTPException(
                    status_code=404, detail=f"Match with ID '{match_id}' not found"
                )

            event = data["events"][0]
            return MatchData(
                event_id=event["idEvent"],
                home_team=event["strHomeTeam"],
                away_team=event["strAwayTeam"],
                home_score=(
                    int(event["intHomeScore"])
                    if event.get("intHomeScore") is not None
                    else None
                ),
                away_score=(
                    int(event["intAwayScore"])
                    if event.get("intAwayScore") is not None
                    else None
                ),
                date_event=event["dateEvent"],
                stadium=event.get("strVenue"),
                league=event.get("strLeague"),
            )

        except httpx.HTTPError as e:
            raise HTTPException(
                status_code=500, detail=f"Error fetching match: {str(e)}"
            )
