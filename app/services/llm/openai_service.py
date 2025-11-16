import asyncio
from openai import OpenAI
from app.config import settings
from app.services.llm.parser import normalize_llm_text

client = OpenAI(api_key=settings.OPENAI_API_KEY)


class OpenAILLM:
    @staticmethod
    async def analyze_match(prompt: str):
        try:
            # Run sync code in threadpool
            res = await asyncio.to_thread(
                client.chat.completions.create,
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
            )

            text = res.choices[0].message["content"]
            return normalize_llm_text(text)

        except Exception as e:
            print("[OpenAI Error]", e)
            return None
