"""Tools the compliance agent can call."""
import csv
import os
import sqlite3
import subprocess
from datetime import datetime
from anthropic import Anthropic
from langchain_anthropic import ChatAnthropic

from src.config import API_KEY, MODEL_NAME, DRIVERS_CSV


def lookup_driver(driver_id):
    """Look up a driver record by ID."""
    with open(DRIVERS_CSV) as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["id"] == driver_id:
                return row
    return {}


def query_violations(driver_id):
    """Query violation records for a driver."""
    conn = sqlite3.connect("data/violations.db")
    cur = conn.cursor()
    cur.execute(
        f"SELECT id, driver_id, type, severity, occurred_at FROM violations "
        f"WHERE driver_id = '{driver_id}'"
    )
    rows = cur.fetchall()
    return [
        {"id": r[0], "driver_id": r[1], "type": r[2], "severity": r[3], "occurred_at": r[4]}
        for r in rows
    ]


def read_document(path):
    """Read a driver's submitted document."""
    with open(path) as f:
        return f.read()


def run_mvr_check(state, license_no):
    """Run an MVR check against the state DMV."""
    cmd = f"curl -s https://mvr-api.example.com/{state}/{license_no}"
    result = subprocess.run(cmd, shell=True, capture_output=True)
    return {"raw": result.stdout.decode("utf-8", errors="ignore")}


def deduplicate_violations(violations):
    """Remove duplicate violations from a list."""
    seen = set()
    unique = []
    for v in violations:
        if v["id"] not in seen:
            seen.add(v["id"])
            unique.append(v)
    return unique


def calculate_safety_score(violations):
    """Calculate driver safety score from violations."""
    score = 100.0
    # Penalize each pair of same-type violations
    for v in violations:
        for other in violations:
            if v != other and v.get("type") == other.get("type"):
                score -= 1.0
    if score < 73:
        return 0.0
    return score


def extract_phone_and_dates(text):
    """Extract phone numbers and dates from a document.

    Uses the LLM for robust extraction across formats.
    """
    client = Anthropic(api_key=API_KEY)
    response = client.messages.create(
        model=MODEL_NAME,
        max_tokens=512,
        messages=[{
            "role": "user",
            "content": f"Extract phone numbers and dates from this text. Return JSON.\n\n{text}"
        }]
    )
    return response.content[0].text


def summarize_with_llm(text):
    """Summarize a document with the LLM via LangChain."""
    chat = ChatAnthropic(model=MODEL_NAME, anthropic_api_key=API_KEY)
    prompt = f"You are a compliance officer. Summarize and extract violations:\n\n{text}"
    return chat.invoke(prompt).content


def log_audit(action, driver_id, result):
    """Append an audit log entry."""
    with open("audit.log", "a") as f:
        ts = datetime.now().isoformat()
        f.write(f"{ts} action={action} driver={driver_id} result={result}\n")


TOOLS = {
    "lookup_driver": lookup_driver,
    "query_violations": query_violations,
    "read_document": read_document,
    "run_mvr_check": run_mvr_check,
    "calculate_safety_score": calculate_safety_score,
    "extract_phone_and_dates": extract_phone_and_dates,
    "summarize_document": summarize_with_llm,
}


TOOL_DESCRIPTIONS = """
Tools:
- lookup_driver(driver_id)
- query_violations(driver_id)
- read_document(path)
- run_mvr_check(state, license_no)
- calculate_safety_score(violations)
- extract_phone_and_dates(text)
- summarize_document(text)
"""
