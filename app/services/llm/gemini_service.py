import asyncio
from google import generativeai as genai
from app.config import settings
from app.services.llm.parser import normalize_llm_text

genai.configure(api_key=settings.GOOGLE_API_KEY)


class GeminiLLM:
    @staticmethod
    async def analyze_match(prompt: str):
        try:
            model = genai.GenerativeModel("gemini-1.5-flash")

            # generate_content() — синхронний метод!
            result = await asyncio.to_thread(model.generate_content, prompt)

            # Try .text (simple responses)
            text = getattr(result, "text", None)

            # Fallback to candidate.content.parts[0].text
            if not text and result.candidates:
                parts = result.candidates[0].content.parts
                if parts and hasattr(parts[0], "text"):
                    text = parts[0].text

            if not text:
                return None

            return normalize_llm_text(text)

        except Exception as e:
            print("[Gemini Error]", e)
            return None
