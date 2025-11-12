import os
import json
import logging
from typing import Optional, List
from dotenv import load_dotenv

from app.models.schemas import MatchAnalysis, MatchData
from app.services.data_processor import DataProcessor

load_dotenv()

from .llm_providers import (
    OpenAIProvider,
    GeminiProvider,
    GroqProvider,
    FatalLLMError,
    TransientLLMError,
    retry_with_backoff,
)

logger = logging.getLogger(__name__)


class LLMService:
    """Orchestrates multiple LLM providers with retries and fallback."""

    def __init__(self, providers: Optional[List] = None):

        self.data_processor = DataProcessor()

        if providers is not None:
            # Allow injecting fake providers for tests
            self.providers = providers
            return

        # Read keys from env
        openai_key = os.getenv("OPENAI_API_KEY")
        gemini_key = os.getenv("GEMINI_API_KEY")
        groq_key = os.getenv("GROQ_API_KEY")

        mapping = {
            "openai": OpenAIProvider(openai_key),
            "gemini": GeminiProvider(gemini_key),
            "groq": GroqProvider(groq_key),
        }

        # Priority order e.g. "openai,gemini,groq" (default)
        priority_env = os.getenv("LLM_PRIORITY", "openai,gemini,groq")
        priority = [p.strip() for p in priority_env.split(",") if p.strip()]

        # Build providers in priority order (only include existing mapping keys)
        self.providers = [mapping[p] for p in priority if p in mapping]

    async def analyze_match(self, match: MatchData) -> MatchAnalysis:
        """Try providers in order, using retry/backoff on transient errors."""
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

        if not self.providers:
            raise RuntimeError(
                "No LLM providers configured (check env keys and LLM_PRIORITY)"
            )

        # Try each provider sequentially. Use retry_with_backoff to retry transient failures.
        for prov in self.providers:
            try:

                async def call() -> str:
                    # provider.generate(prompt) is expected to raise TransientLLMError or FatalLLMError on problems
                    return await prov.generate(prompt)

                # specify retries (e.g., 2 retries => 3 attempts)
                text = await retry_with_backoff(call, retries=2, base_delay=0.5)
                # parse and return first successful response
                return self._parse_analysis(text)

            except FatalLLMError as e:
                # non-retryable / provider won't help (e.g., quota, missing key)
                logger.warning(
                    "Provider %s fatal error: %s",
                    getattr(prov, "name", str(prov)),
                    str(e),
                )
                continue
            except TransientLLMError as e:
                # retries exhausted but provider failed transiently
                logger.warning(
                    "Provider %s transient failure after retries: %s",
                    getattr(prov, "name", str(prov)),
                    str(e),
                )
                continue
            except Exception as e:
                # unexpected error from provider; skip to next
                logger.exception(
                    "Provider %s unexpected error: %s",
                    getattr(prov, "name", str(prov)),
                    str(e),
                )
                continue

        # If all providers fail:
        logger.error("All LLM providers failed.")
        raise RuntimeError("All LLM providers failed.")

    def _parse_analysis(self, text: str) -> MatchAnalysis:
        """
        Parse text returned by LLM. Prefer JSON text; fallback to extracting the first JSON object
        from the response if there is extra commentary around it.
        """
        text = (text or "").strip()
        if not text:
            raise ValueError("Empty response from LLM provider")

        # Try JSON directly first
        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            # Fallback: find the first {...} block and parse that
            start = text.find("{")
            end = text.rfind("}") + 1
            if start == -1 or end == 0:
                raise ValueError("No JSON found in LLM response")
            json_text = text[start:end]
            try:
                data = json.loads(json_text)
            except json.JSONDecodeError as e:
                raise ValueError("Failed to decode JSON from LLM response") from e

        # Coerce fields safely
        summary = data.get("summary", "") if isinstance(data, dict) else ""
        key_insights = data.get("key_insights", []) if isinstance(data, dict) else []
        if not isinstance(key_insights, list):
            # defensive: coerce single string into list
            key_insights = [str(key_insights)]
        key_insights = [str(i).strip() for i in key_insights if str(i).strip()]
        performance_analysis = (
            data.get("performance_analysis", "") if isinstance(data, dict) else ""
        )
        prediction = data.get("prediction") if isinstance(data, dict) else None

        return MatchAnalysis(
            summary=summary,
            key_insights=key_insights,
            performance_analysis=performance_analysis,
            prediction=prediction,
        )
