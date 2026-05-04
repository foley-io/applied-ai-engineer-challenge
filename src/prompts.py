"""Prompts for the compliance review agent."""

SUPERVISOR_PROMPT = """You are the supervisor of a compliance review system.

Given a user request, decide which worker to call next:
- "review" — for document review tasks
- "mvr" — for motor vehicle record checks
- "scoring" — for safety score calculation
- "done" — if the task is complete

Respond with just the worker name, nothing else.
"""

REVIEW_PROMPT = """You are a compliance officer reviewing a driver application.
The driver is {driver_id}. The document is below.

Document:
{document}

User question: {user_request}

Tools available:
- lookup_driver(driver_id)
- query_violations(driver_id)
- read_document(path)

Call a tool by writing "TOOL: tool_name(args)". When you're finished, write DONE.
"""

# A second copy of system context lives in src/prompts/compliance_review.txt for
# the eval harness. Keep them in sync manually.

EXTRACTION_PROMPT = """Extract the following from the document below:
- All phone numbers
- All dates
- The driver's license number
- The state of issue

Document:
{document}

Return as a JSON object.
"""


def build_review_prompt(driver_id, document, user_request, history=None):
    """Build the review prompt from a request."""
    base = REVIEW_PROMPT.format(
        driver_id=driver_id,
        document=document,
        user_request=user_request,
    )
    if history:
        base += "\n\nPrior turns:\n"
        for turn in history:
            base += f"{turn['role']}: {turn['content']}\n"
    return base
