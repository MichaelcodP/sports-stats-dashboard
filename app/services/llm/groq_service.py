import asyncio
from groq import Groq
from app.config import settings
from app.services.llm.parser import normalize_llm_text

client = Groq(api_key=settings.GROQ_API_KEY)


class GroqLLM:
    @staticmethod
    async def analyze_match(prompt: str):
        try:
            res = await asyncio.to_thread(
                client.chat.completions.create,
                model="llama3-70b-8192",
                messages=[{"role": "user", "content": prompt}],
            )

            text = res.choices[0].message["content"]
            return normalize_llm_text(text)

        except Exception as e:
            print("[Groq Error]", e)
            return None
