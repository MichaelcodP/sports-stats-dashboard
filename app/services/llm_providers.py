import asyncio
from typing import Optional
import httpx
from openai import AsyncOpenAI


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
        url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent"
        headers = {"Authorization": f"Bearer {self.api_key}"}
        payload = {"contents": [{"parts": [{"text": prompt}]}]}
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    url, headers=headers, json=payload, timeout=15.0
                )
                resp.raise_for_status()
                result = resp.json()
                text = result["candidates"][0]["content"]["parts"][0]["text"]
                return text.strip()
        except httpx.HTTPStatusError as e:
            code = e.response.status_code
            if code >= 500:
                raise TransientLLMError(str(e))
            raise FatalLLMError(str(e))
        except Exception as e:
            raise TransientLLMError(str(e))


class GroqProvider(BaseProvider):
    name = "groq"

    def __init__(self, api_key: Optional[str]):
        self.api_key = api_key

    async def generate(self, prompt: str) -> str:
        if not self.api_key:
            raise FatalLLMError("Groq key not provided")
        url = "https://api.groq.com/v1/chat/completions"
        headers = {"Authorization": f"Bearer {self.api_key}"}
        payload = {
            "model": "mixtral-8x7b-32768",
            "messages": [
                {"role": "system", "content": "You are a professional soccer analyst."},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.7,
            "max_tokens": 500,
        }
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    url, headers=headers, json=payload, timeout=15.0
                )
                resp.raise_for_status()
                result = resp.json()
                return result["choices"][0]["message"]["content"].strip()
        except httpx.HTTPStatusError as e:
            if e.response.status_code >= 500:
                raise TransientLLMError(str(e))
            raise FatalLLMError(str(e))
        except Exception as e:
            raise TransientLLMError(str(e))


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
