import pandas as pd
from app.models.schemas import MatchData


class DataProcessor:
    """Process match data using Pandas."""

    def process_match_data(self, match: MatchData) -> pd.DataFrame:
        """Convert match data to DataFrame."""
        data = {
            "Team": [match.home_team, match.away_team],
            "Score": [match.home_score or 0, match.away_score or 0],
            "Location": ["Home", "Away"],
        }

        df = pd.DataFrame(data)
        df["Goal_Difference"] = df["Score"] - df["Score"].iloc[::-1].values
        df["Result"] = df["Goal_Difference"].apply(
            lambda x: "Win" if x > 0 else ("Loss" if x < 0 else "Draw")
        )

        return df

    def calculate_statistics(self, match: MatchData) -> dict:
        """Calculate match statistics."""
        df = self.process_match_data(match)

        total_goals = (match.home_score or 0) + (match.away_score or 0)
        goal_diff = abs((match.home_score or 0) - (match.away_score or 0))

        winner = (
            df[df["Result"] == "Win"]["Team"].values[0]
            if "Win" in df["Result"].values
            else "Draw"
        )

        return {
            "total_goals": total_goals,
            "goal_difference": goal_diff,
            "winner": winner,
            "match_competitiveness": ("Close" if goal_diff <= 1 else "Dominant"),
            "home_advantage": (match.home_score or 0) > (match.away_score or 0),
        }

    def format_for_llm(self, match: MatchData) -> str:
        """Format match data for LLM analysis."""
        stats = self.calculate_statistics(match)
        df = self.process_match_data(match)

        return f"""
Match Details:
- Date: {match.date_event}
- Stadium: {match.stadium or 'Unknown'}
- League: {match.league or 'Unknown'}

Teams and Scores:
- Home: {match.home_team} ({match.home_score or 0} goals)
- Away: {match.away_team} ({match.away_score or 0} goals)

Statistics:
- Total Goals: {stats['total_goals']}
- Winner: {stats['winner']}
- Match Type: {stats['match_competitiveness']}
- Home Advantage: {'Yes' if stats['home_advantage'] else 'No'}

Performance Data:
{df.to_string(index=False)}
""".strip()
