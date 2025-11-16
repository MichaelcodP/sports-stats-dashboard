import re


def extract_section(text: str, section: str) -> str:
    pattern = rf"{section}:(.*?)(\n[A-Z][a-zA-Z ]+:|$)"
    match = re.search(pattern, text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return ""


def extract_list_section(text: str, section: str) -> list:
    raw = extract_section(text, section)
    return [line.strip("- •").strip() for line in raw.split("\n") if line.strip()]


def normalize_llm_text(text: str) -> dict:
    return {
        "summary": extract_section(text, "Summary"),
        "key_insights": extract_list_section(text, "Key Insights"),
        "performance_analysis": extract_section(text, "Performance Analysis"),
        "prediction": extract_section(text, "Prediction"),
    }
