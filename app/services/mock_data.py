from app.models.schemas import TeamInfo
import random
from datetime import datetime, timedelta
from typing import List


class MockSportsData:
    """Mock data service for when TheSportsDB API is unavailable."""

    MOCK_TEAMS = {
        "arsenal": {
            "id": "133604",
            "name": "Arsenal",
            "country": "England",
            "sport": "Soccer",
            "league": "Premier League",
        },
        "chelsea": {
            "id": "133610",
            "name": "Chelsea",
            "country": "England",
            "sport": "Soccer",
            "league": "Premier League",
        },
        "liverpool": {
            "id": "133602",
            "name": "Liverpool",
            "country": "England",
            "sport": "Soccer",
            "league": "Premier League",
        },
        "manchester united": {
            "id": "133612",
            "name": "Manchester United",
            "country": "England",
            "sport": "Soccer",
            "league": "Premier League",
        },
        "manchester city": {
            "id": "133613",
            "name": "Manchester City",
            "country": "England",
            "sport": "Soccer",
            "league": "Premier League",
        },
        "brighton and hove albion": {
            "id": "133619",
            "name": "Brighton and Hove Albion",
            "country": "England",
            "sport": "Soccer",
            "league": "Premier League",
        },
    }

    @staticmethod
    def get_mock_team(team_name: str) -> TeamInfo:
        """Get mock team data."""
        team_lower = team_name.lower()
        # Try exact match first
        team_data = MockSportsData.MOCK_TEAMS.get(team_lower)
        if team_data:
            return TeamInfo(
                id=team_data["id"],
                name=team_data["name"],
                country=team_data["country"],
                sport=team_data["sport"],
                league=team_data["league"],
            )

        # Try partial matches
        for key, data in MockSportsData.MOCK_TEAMS.items():
            if key in team_lower or team_lower in key:
                return TeamInfo(
                    id=data["id"],
                    name=data["name"],
                    country=data["country"],
                    sport=data["sport"],
                    league=data["league"],
                )

        # Return Arsenal as default
        team_data = MockSportsData.MOCK_TEAMS["arsenal"]
        return TeamInfo(
            id=team_data["id"],
            name=team_data["name"],
            country=team_data["country"],
            sport=team_data["sport"],
            league=team_data["league"],
        )

    @staticmethod
    def get_mock_matches(team_id: str, limit: int = 5) -> List[dict]:
        """Generate mock match data."""
        # Real Premier League teams for more realistic data
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
            "Brentford",
            "Aston Villa",
            "Wolverhampton",
            "Southampton",
            "Everton",
            "Nottingham Forest",
            "Leicester City",
            "Ipswich Town",
            "West Ham",
            "Bournemouth",
        ]

        # Get team name from ID
        team_name = "Arsenal"  # Default
        for team_data in MockSportsData.MOCK_TEAMS.values():
            if team_data["id"] == team_id:
                team_name = team_data["name"]
                break

        # Remove the current team from opponents
        available_opponents = [t for t in premier_league_teams if t != team_name]

        matches = []
        base_date = datetime.now() - timedelta(days=30)

        for i in range(limit):
            match_date = base_date - timedelta(days=i * 7)  # One match per week

            # Random scores
            home_score = random.randint(0, 4)
            away_score = random.randint(0, 4)

            # Alternate home/away
            is_home = i % 2 == 0

            # Choose a random opponent
            opponent = random.choice(available_opponents)

            match = {
                "idEvent": f"mock_{team_id}_{i}",
                "strHomeTeam": team_name if is_home else opponent,
                "strAwayTeam": opponent if is_home else team_name,
                "intHomeScore": home_score if is_home else away_score,
                "intAwayScore": away_score if is_home else home_score,
                "dateEvent": match_date.strftime("%Y-%m-%d"),
                "strVenue": (
                    f"{team_name} Stadium" if is_home else f"{opponent} Stadium"
                ),
                "strLeague": "Premier League",
            }
            matches.append(match)

        return matches
