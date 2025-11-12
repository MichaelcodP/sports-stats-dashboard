import asyncio
import json
import os
from dotenv import load_dotenv
from openai import AsyncOpenAI
import httpx
from app.models.schemas import MatchAnalysis, MatchData
from app.services.data_processor import DataProcessor

load_dotenv()


class LLMService:
    """Service for LLM-based operations."""

    def __init__(self):
        self.keys = {
            "openai": os.getenv("OPENAI_API_KEY"),
            "gemini": os.getenv("GEMINI_API_KEY"),
            "groq": os.getenv("GROQ_API_KEY"),
        }
        self.data_processor = DataProcessor()

    async def analyze_match(self, match: MatchData) -> MatchAnalysis:
        formatted_data = self.data_processor.format_for_llm(match)
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

        # Each LLM is called in parallel
        tasks = [
            self._call_llm(provider, prompt)
            for provider, key in self.keys.items()
            if key
        ]

        for coro in asyncio.as_completed(tasks):
            try:
                analysis_text = await coro
                return self._parse_analysis(analysis_text)
            except Exception as e:
                print(f"LLM failed: {e}")

        raise RuntimeError("All LLM providers failed.")

    async def _call_llm(self, provider: str, prompt: str) -> str:
        if provider == "openai":
            client = AsyncOpenAI(api_key=self.keys["openai"])
            response = await client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a professional soccer analyst.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.7,
                max_tokens=500,
            )
            return response.choices[0].message.content.strip()

        elif provider == "gemini":
            async with httpx.AsyncClient() as client:
                url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent"
                headers = {"Authorization": f"Bearer {self.keys['gemini']}"}
                payload = {"contents": [{"parts": [{"text": prompt}]}]}
                resp = await client.post(url, headers=headers, json=payload)
                resp.raise_for_status()
                result = resp.json()
                return result["candidates"][0]["content"]["parts"][0]["text"].strip()

        elif provider == "groq":
            async with httpx.AsyncClient() as client:
                url = "https://api.groq.com/v1/chat/completions"
                headers = {"Authorization": f"Bearer {self.keys['groq']}"}
                payload = {
                    "model": "mixtral-8x7b-32768",
                    "messages": [
                        {
                            "role": "system",
                            "content": "You are a professional soccer analyst.",
                        },
                        {"role": "user", "content": prompt},
                    ],
                    "temperature": 0.7,
                    "max_tokens": 500,
                }
                resp = await client.post(url, headers=headers, json=payload)
                resp.raise_for_status()
                result = resp.json()
                return result["choices"][0]["message"]["content"].strip()

        raise ValueError(f"Unknown LLM provider: {provider}")

    def _parse_analysis(self, text: str) -> MatchAnalysis:
        """Parse LLM response into structured JSON format."""
        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            # Back-up for extra text before JSON
            start = text.find("{")
            end = text.rfind("}") + 1
            if start == -1 or end == -1:
                raise ValueError("No JSON found in LLM response")
            data = json.loads(text[start:end])

        return MatchAnalysis(
            summary=data.get("summary", ""),
            key_insights=data.get("key_insights", []),
            performance_analysis=data.get("performance_analysis", ""),
            prediction=data.get("prediction"),
        )
