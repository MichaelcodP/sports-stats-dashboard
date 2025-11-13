from typing import List, Dict
from threading import Lock


class MatchStore:
    def __init__(self):
        self.matches: List[Dict] = []
        self._lock = Lock()

    def update_matches(self, matches: List[Dict]):
        with self._lock:
            self.matches = matches

    def get_all(self) -> List[Dict]:
        with self._lock:
            return self.matches.copy()

    def filter_by_team(self, team_name: str) -> List[Dict]:
        """Filter matches by team name."""
        with self._lock:
            return [
                match
                for match in self.matches
                if match.get("strHomeTeam", "").lower() == team_name.lower()
                or match.get("strAwayTeam", "").lower() == team_name.lower()
            ]

    def filter_by_opponent(self, team_name: str, opponent_name: str) -> List[Dict]:
        """Filter matches by team and opponent."""
        with self._lock:
            return [
                match
                for match in self.matches
                if (
                    match.get("strHomeTeam", "").lower() == team_name.lower()
                    and match.get("strAwayTeam", "").lower() == opponent_name.lower()
                )
                or (
                    match.get("strAwayTeam", "").lower() == team_name.lower()
                    and match.get("strHomeTeam", "").lower() == opponent_name.lower()
                )
            ]


match_store = MatchStore()
