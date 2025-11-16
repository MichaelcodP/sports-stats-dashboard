import os
import json
import logging
from typing import Optional, List, Dict
from dotenv import load_dotenv

from app.models.schemas import MatchAnalysis, MatchData
from app.services.data_processor import DataProcessor
from app.services.cache import CacheService

from .llm_providers import (
    OpenAIProvider,
    GeminiProvider,
    GroqProvider,
    # FatalLLMError,
    # TransientLLMError,
    retry_with_backoff,
)

load_dotenv()

logger = logging.getLogger(__name__)


class LLMService:
    """LLM orchestration with caching + multi-provider support."""

    def __init__(self, providers: Optional[List] = None):
        self.data_processor = DataProcessor()
        self.cache = CacheService()

        if providers is not None:
            self.providers = providers
            return

        openai_key = os.getenv("OPENAI_API_KEY")
        gemini_key = os.getenv("GEMINI_API_KEY")
        groq_key = os.getenv("GROQ_API_KEY")

        self.providers = {
            "openai": OpenAIProvider(openai_key),
            "gemini": GeminiProvider(gemini_key),
            "groq": GroqProvider(groq_key),
        }

    async def analyze_with_all_models(self, match: MatchData) -> Dict:
        """
        Returns analysis from ALL LLM providers:
        {
            "openai": MatchAnalysis,
            "gemini": MatchAnalysis,
            "groq": MatchAnalysis
        }
        """

        if not match.event_id:
            raise ValueError("Match must have event_id for caching")

        formatted_data = self.data_processor.format_for_llm(match)

        prompt = f"""
Respond with ONLY valid JSON matching:

{{
  "summary": "<2-3 sentence summary>",
  "key_insights": ["insight1", "insight2"],
  "performance_analysis": "<text>",
  "prediction": "<text or null>"
}}

Analyze this match:
{formatted_data}
"""

        results = {}

        # RUN ALL MODELS ONE BY ONE
        for name, provider in self.providers.items():
            cache_key = f"match:{match.event_id}:model:{name}"

            # 1 — CACHE CHECK
            cached = await self.cache.get(cache_key)
            if cached:
                logger.info(f"[CACHE HIT] model={name} event={match.event_id}")
                results[name] = MatchAnalysis(**cached)
                continue

            logger.info(f"[CACHE MISS] model={name}")

            # 2 — CALL LLM
            try:

                async def call():
                    return await provider.generate(prompt)

                raw = await retry_with_backoff(call, retries=2)

                parsed = self._parse_analysis(raw)

                # 3 — SAVE CACHE
                await self.cache.set(cache_key, parsed.model_dump())

                results[name] = parsed

            except Exception as e:
                logger.error(f"[LLM FAIL] {name}: {str(e)}")
                results[name] = None

        return results

    async def analyze_match(self, match: MatchData) -> MatchAnalysis:
        if not match.event_id:
            raise ValueError("Match must have event_id for caching.")

        cache_key = f"match:{match.event_id}:analysis"

        cached = await self.cache.get(cache_key)
        if cached:
            return MatchAnalysis(**cached)

        formatted_data = self.data_processor.format_for_llm(match)

        prompt = f"""
Respond with ONLY valid JSON matching:

{{
  "summary": "<2-3 sentence summary>",
  "key_insights": ["insight1", "insight2"],
  "performance_analysis": "<text>",
  "prediction": "<text or null>"
}}

Analyze this match:
{formatted_data}
"""

        for prov in self.providers:
            try:
                async def call():
                    return await prov.generate(prompt)

                text = await retry_with_backoff(call, retries=2, base_delay=0.5)
                analysis = self._parse_analysis(text)

                await self.cache.set(cache_key, analysis.model_dump())
                return analysis

            except Exception:
                continue

        raise RuntimeError("All LLM providers failed")

    def _parse_analysis(self, text: str) -> MatchAnalysis:
        text = (text or "").strip()
        if not text:
            raise ValueError("Empty LLM response")

        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            start = text.find("{")
            end = text.rfind("}") + 1
            data = json.loads(text[start:end])

        key_insights = data.get("key_insights", [])
        if isinstance(key_insights, str):
            key_insights = [key_insights]

        return MatchAnalysis(
            summary=data.get("summary", ""),
            key_insights=key_insights,
            performance_analysis=data.get("performance_analysis", ""),
            prediction=data.get("prediction"),
        )
