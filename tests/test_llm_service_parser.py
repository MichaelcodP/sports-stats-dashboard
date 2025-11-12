import json
import pytest

from app.services.llm_service import LLMService
from app.models.schemas import MatchAnalysis


def test_parse_json_direct():
    svc = LLMService(providers=[])
    payload = {
        "summary": "Barcelona controlled possession and scored twice.",
        "key_insights": ["Possession advantage", "Clinical finishing"],
        "performance_analysis": "Barcelona dominated midfield and created high-xG chances.",
        "prediction": "Barcelona favored",
    }
    text = json.dumps(payload)
    result = svc._parse_analysis(text)

    assert isinstance(result, MatchAnalysis)
    assert "Barcelona controlled" in result.summary
    assert result.key_insights == ["Possession advantage", "Clinical finishing"]
    assert "dominated midfield" in result.performance_analysis
    assert result.prediction == "Barcelona favored"


def test_parse_with_extra_text():
    svc = LLMService(providers=[])
    payload = {
        "summary": "Chelsea executed a defensive gameplan.",
        "key_insights": ["Low possession", "Effective counters"],
        "performance_analysis": "Chelsea sat deep and struck on the break.",
        "prediction": None,
    }
    messy = (
        "Note: below is the analysis you requested.\n"
        + json.dumps(payload)
        + "\n-- end --"
    )
    result = svc._parse_analysis(messy)

    assert isinstance(result, MatchAnalysis)
    assert result.summary.startswith("Chelsea executed")
    assert len(result.key_insights) == 2
    assert "struck on the break" in result.performance_analysis


def test_parse_invalid_json_raises():
    svc = LLMService(providers=[])
    bad = "{summary: 'invalid json'}"  # not valid JSON
    with pytest.raises(ValueError):
        svc._parse_analysis(bad)


def test_key_insights_coerce_single_string():
    svc = LLMService(providers=[])
    payload = {
        "summary": "Single insight example.",
        "key_insights": "Only one insight string",
        "performance_analysis": "Short analysis.",
        "prediction": None,
    }
    text = json.dumps(payload)
    result = svc._parse_analysis(text)

    assert isinstance(result, MatchAnalysis)
    assert result.key_insights == ["Only one insight string"]


def test_empty_response_raises():
    svc = LLMService(providers=[])
    with pytest.raises(ValueError):
        svc._parse_analysis("")
