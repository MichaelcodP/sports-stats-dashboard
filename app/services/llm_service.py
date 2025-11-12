import json
import os
import re
from dotenv import load_dotenv
from openai import AsyncOpenAI
from app.models.schemas import MatchAnalysis, MatchData
from app.services.data_processor import DataProcessor

load_dotenv()

class LLMService:
    """Service for LLM-based operations."""

    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.client = AsyncOpenAI(api_key=self.api_key)
        self.data_processor = DataProcessor()

    async def analyze_match(self, match: MatchData) -> MatchAnalysis:
        """Analyze match data using LLM."""
        # Format match data
        formatted_data = self.data_processor.format_for_llm(match)

        # Prompt for LLM
        prompt = f"""
Respond with ONLY valid JSON matching this schema (no explanatory text):

{{
      "summary": "<2-3 sentence summary>",
      "key_insights": ["insight1", "insight2", "..."],
      "performance_analysis": "<detailed text>",
      "prediction": "<prediction string or null>"
}}

Now analyze this match:
{formatted_data}
"""

        # Call OpenAI API
        response = await self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a professional soccer analyst."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.7,
            max_tokens=500,
        )

        analysis_text = response.choices[0].message.content.strip()
        return self._parse_analysis(analysis_text)

    def _parse_analysis(self, text: str) -> MatchAnalysis:
        """Parse LLM response into structured JSON format."""
        text = (text or "").strip()
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if not match:
            raise ValueError("No JSON found in LLM response")

        data = json.loads(match.group(0))
        return MatchAnalysis(
            summary=data.get("summary", ""),
            key_insights=data.get("key_insights", []),
            performance_analysis=data.get("performance_analysis", ""),
            prediction=data.get("prediction"),
        )
