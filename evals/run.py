"""Eval runner.

Runs the agent against a small set of cases and reports a score.
"""
import json
from anthropic import Anthropic

from src.agent import run_agent
from src.config import API_KEY, MODEL_NAME


JUDGE_PROMPT = """You are evaluating an agent's response. Read the request and
the response, and tell me if the response is good. Reply with just YES or NO.

Request: {request}

Response: {response}
"""


def judge(request, response):
    """Ask the LLM whether a response is good."""
    client = Anthropic(api_key=API_KEY)
    out = client.messages.create(
        model=MODEL_NAME,
        max_tokens=5,
        messages=[{
            "role": "user",
            "content": JUDGE_PROMPT.format(request=request, response=response),
        }]
    )
    return "yes" in out.content[0].text.lower()


def main():
    with open("evals/cases.json") as f:
        cases = json.load(f)

    correct = 0
    for case in cases:
        response = run_agent(case["request"], driver_id=case.get("driver_id"))
        if judge(case["request"], response):
            correct += 1
            print(f"PASS: {case['request']}")
        else:
            print(f"FAIL: {case['request']}")

    accuracy = correct / len(cases)
    print(f"\nAccuracy: {accuracy:.0%}")
    print(f"Score: {correct}/{len(cases)}")


if __name__ == "__main__":
    main()
