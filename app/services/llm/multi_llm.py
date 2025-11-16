from app.services.llm.openai_service import OpenAILLM
from app.services.llm.gemini_service import GeminiLLM
from app.services.llm.groq_service import GroqLLM


class MultiLLMService:
    @staticmethod
    async def analyze_with_all(prompt: str):
        return {
            "openai": await OpenAILLM.analyze_match(prompt),
            "gemini": await GeminiLLM.analyze_match(prompt),
            "groq": await GroqLLM.analyze_match(prompt),
        }
