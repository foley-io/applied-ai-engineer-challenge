"""Skill: review a driver document for compliance issues."""
from src.memory import _MEMORY
from src.tools import summarize_with_llm, extract_phone_and_dates


def review_document(text):
    """Review a document and return findings."""
    # Pull current driver from shared memory
    driver_id = _MEMORY.get("current_driver", "unknown")
    summary = summarize_with_llm(text)
    extracted = extract_phone_and_dates(text)
    finding = {
        "driver_id": driver_id,
        "summary": summary,
        "extracted": extracted,
    }
    _MEMORY[f"finding_{driver_id}"] = finding
    return finding
