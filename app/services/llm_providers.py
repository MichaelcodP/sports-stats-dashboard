import asyncio
from typing import Optional
from openai import AsyncOpenAI
import google.generativeai as genai
from groq import Groq


class LLMProviderError(Exception):
    """Base provider error."""


class TransientLLMError(LLMProviderError):
    """Transient error (retryable)."""


class FatalLLMError(LLMProviderError):
    """Non-retryable error."""


class BaseProvider:
    name: str

    async def generate(self, prompt: str) -> str:
        """Generate text for prompt. Should raise LLMProviderError on failure."""
        raise NotImplementedError()


class OpenAIProvider(BaseProvider):
    name = "openai"

    def __init__(self, api_key: Optional[str]):
        self.api_key = api_key

    async def generate(self, prompt: str) -> str:
        if not self.api_key:
            raise FatalLLMError("OpenAI key not provided")
        try:
            client = AsyncOpenAI(api_key=self.api_key)
            resp = await client.chat.completions.create(
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
            # defensive extraction
            choice = resp.choices[0]
            if hasattr(choice, "message"):
                content = getattr(choice.message, "content", None)
                if isinstance(choice.message, dict):
                    content = content or choice.message.get("content")
            else:
                content = getattr(choice, "text", None) or (
                    choice.get("text") if isinstance(choice, dict) else None
                )
            if not content:
                raise TransientLLMError("No content from OpenAI")
            return content.strip()
        except Exception as exc:
            # check exc for quota/insufficient_quota and raise FatalLLMError or TransientLLMError
            msg = str(exc)
            if "quota" in msg.lower() or "insufficient_quota" in msg.lower():
                raise FatalLLMError(msg)
            # treat network/other issues as transient
            raise TransientLLMError(msg)


class GeminiProvider(BaseProvider):
    name = "gemini"

    def __init__(self, api_key: Optional[str]):
        self.api_key = api_key

    async def generate(self, prompt: str) -> str:
        if not self.api_key:
            raise FatalLLMError("Gemini key not provided")

        try:
            genai.configure(api_key=self.api_key)
            model = genai.GenerativeModel("gemini-2.0-flash")
            response = await asyncio.to_thread(model.generate_content, prompt)
            return response.text.strip()
        except Exception as exc:
            msg = str(exc)
            if "quota" in msg.lower() or "billing" in msg.lower():
                raise FatalLLMError(msg)
            raise TransientLLMError(msg)


class GroqProvider(BaseProvider):
    name = "groq"

    def __init__(self, api_key: Optional[str]):
        self.api_key = api_key

    async def generate(self, prompt: str) -> str:
        if not self.api_key:
            raise FatalLLMError("Groq key not provided")

        try:
            client = Groq(api_key=self.api_key)
            response = await asyncio.to_thread(
                client.chat.completions.create,
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=500,
                temperature=0.7,
            )
            return response.choices[0].message.content.strip()
        except Exception as exc:
            msg = str(exc)
            if "quota" in msg.lower() or "billing" in msg.lower():
                raise FatalLLMError(msg)
            raise TransientLLMError(msg)


# retry/backoff helper
async def retry_with_backoff(coro, retries: int = 2, base_delay: float = 0.5):
    last_exc = None
    for attempt in range(retries + 1):
        try:
            return await coro()
        except TransientLLMError as e:
            last_exc = e
            delay = base_delay * (2**attempt)
            await asyncio.sleep(delay)
        except FatalLLMError:
            # stop retries on fatal errors
            raise
    raise last_exc or Exception("Retries exhausted")
