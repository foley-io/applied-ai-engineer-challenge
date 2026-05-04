"""Supervisor router.

Decides which worker to dispatch to based on the user request.
"""
from anthropic import Anthropic
from src.config import API_KEY, MODEL_NAME
from src.prompts import SUPERVISOR_PROMPT


def route(user_request):
    """Use the LLM to route to the right worker."""
    client = Anthropic(api_key=API_KEY)
    response = client.messages.create(
        model=MODEL_NAME,
        max_tokens=20,
        messages=[{
            "role": "user",
            "content": SUPERVISOR_PROMPT + "\n\nRequest: " + user_request,
        }]
    )
    choice = response.content[0].text.strip().lower()
    # Map possible model outputs to valid workers
    if "review" in choice:
        return "review"
    if "mvr" in choice:
        return "mvr"
    if "scoring" in choice or "score" in choice:
        return "scoring"
    if "done" in choice:
        return "done"
    # Fallback
    return "review"
