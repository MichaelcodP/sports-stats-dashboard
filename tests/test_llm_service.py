import pytest
from app.services.llm_service import LLMService
from app.models.schemas import MatchAnalysis


@pytest.mark.asyncio
async def test_parse_valid_json(monkeypatch):
    service = LLMService()

    fake_response = """
    {
        "summary": "Barcelona dominated the match.",
        "key_insights": ["Messi played well", "Strong defense"],
        "performance_analysis": "Barcelona controlled possession throughout.",
        "prediction": "Barcelona likely to win next match"
    }
    """

    result = service._parse_analysis(fake_response)
    assert isinstance(result, MatchAnalysis)
    assert "Barcelona" in result.summary
    assert len(result.key_insights) == 2
    assert result.prediction is not None


@pytest.mark.asyncio
async def test_parse_with_extra_text(monkeypatch):
    service = LLMService()
    messy_response = (
        "Here is your analysis:\n"
        + """
    {
        "summary": "Chelsea played defensively.",
        "key_insights": ["Low possession", "Counter attacks"],
        "performance_analysis": "Chelsea relied on counter-attacks.",
        "prediction": null
    }
    """
        + "\nThanks!"
    )

    result = service._parse_analysis(messy_response)
    assert result.summary.startswith("Chelsea")
    assert "counter" in result.performance_analysis.lower()


@pytest.mark.asyncio
async def test_parse_invalid_json(monkeypatch):
    """If the JSON is broken, we expect a ValueError."""
    service = LLMService()
    bad_response = "{summary: 'invalid json'}"

    with pytest.raises(ValueError):
        service._parse_analysis(bad_response)
