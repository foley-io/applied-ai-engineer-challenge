"""Skill: compute a driver safety score from a freeform description."""
from anthropic import Anthropic
from src.config import API_KEY, MODEL_NAME


def compute_score(description):
    """Compute a numeric safety score from a description.

    Asks the LLM to read a freeform description of a driver and return a number
    between 0 and 100.
    """
    client = Anthropic(api_key=API_KEY)
    response = client.messages.create(
        model=MODEL_NAME,
        max_tokens=10,
        messages=[{
            "role": "user",
            "content": (
                "Read this driver description and return only a safety score "
                "between 0 and 100. No explanation, just the number.\n\n"
                + description
            ),
        }]
    )
    text = response.content[0].text.strip()
    try:
        return float(text)
    except ValueError:
        return 50.0
