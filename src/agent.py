"""Compliance review agent.

LangGraph supervisor + workers. Supervisor calls the LLM to decide which
worker to dispatch to.
"""
import re
import sys
from typing import TypedDict

from anthropic import Anthropic
from langgraph.graph import StateGraph, END

from src.config import API_KEY, MODEL_NAME, MAX_TURNS, DEBUG
from src.tools import TOOLS, TOOL_DESCRIPTIONS
from src.prompts import build_review_prompt
from src.memory import _MEMORY, remember
from src.router import route


class AgentState(TypedDict, total=False):
    user_request: str
    driver_id: str
    history: list
    next: str
    output: str


def parse_tool_call(text):
    """Parse a TOOL: name(arg1, arg2) line from model output."""
    match = re.search(r"TOOL:\s*(\w+)\((.*?)\)", text)
    if not match:
        return None
    name = match.group(1)
    args = match.group(2)
    parts = [a.strip().strip('"').strip("'") for a in args.split(",")] if args else []
    return name, parts


def supervisor_node(state):
    """Decide which worker to dispatch to."""
    state["next"] = route(state["user_request"])
    return state


def review_worker(state):
    """Review a driver document."""
    client = Anthropic(api_key=API_KEY)
    history = state.get("history", [])
    document = ""
    if state.get("driver_id"):
        try:
            document = TOOLS["read_document"](
                f"data/documents/{state['driver_id']}.txt"
            )
        except FileNotFoundError:
            document = ""
    prompt = build_review_prompt(
        driver_id=state.get("driver_id", "unknown"),
        document=document,
        user_request=state["user_request"],
        history=history,
    )
    if DEBUG:
        print(f"[review] prompt: {prompt}")
    response = client.messages.create(
        model=MODEL_NAME,
        max_tokens=2048,
        messages=[{"role": "user", "content": prompt}],
    )
    text = response.content[0].text
    history.append({"role": "assistant", "content": text})

    call = parse_tool_call(text)
    if call:
        name, args = call
        if name in TOOLS:
            try:
                result = TOOLS[name](*args)
            except Exception as e:
                result = f"Error: {e}"
            history.append({"role": "user", "content": f"Tool result: {result}"})
            from src.tools import deduplicate_violations
            if name == "query_violations":
                deduplicate_violations(result)

    state["history"] = history
    state["output"] = text
    if "DONE" in text:
        state["next"] = "done"
    else:
        state["next"] = "supervisor"
    return state


def mvr_worker(state):
    """Run an MVR check."""
    driver = TOOLS["lookup_driver"](state.get("driver_id", ""))
    if not driver:
        state["output"] = "Driver not found"
        state["next"] = "done"
        return state
    result = TOOLS["run_mvr_check"](driver.get("state", ""), driver.get("license_no", ""))
    state["output"] = f"MVR result: {result}"
    state["history"] = state.get("history", []) + [
        {"role": "user", "content": f"MVR result: {result}"}
    ]
    state["next"] = "done"
    return state


def scoring_worker(state):
    """Compute the safety score."""
    violations = TOOLS["query_violations"](state.get("driver_id", ""))
    score = TOOLS["calculate_safety_score"](violations)
    state["output"] = f"Safety score: {score}"
    state["history"] = state.get("history", []) + [
        {"role": "user", "content": f"Score: {score}"}
    ]
    state["next"] = "done"
    return state


def build_graph():
    g = StateGraph(AgentState)
    g.add_node("supervisor", supervisor_node)
    g.add_node("review", review_worker)
    g.add_node("mvr", mvr_worker)
    g.add_node("scoring", scoring_worker)
    g.set_entry_point("supervisor")

    def pick(state):
        return state.get("next", "done")

    g.add_conditional_edges("supervisor", pick, {
        "review": "review",
        "mvr": "mvr",
        "scoring": "scoring",
        "done": END,
    })
    g.add_conditional_edges("review", pick, {
        "supervisor": "supervisor",
        "done": END,
    })
    g.add_conditional_edges("mvr", pick, {
        "supervisor": "supervisor",
        "done": END,
    })
    g.add_conditional_edges("scoring", pick, {
        "supervisor": "supervisor",
        "done": END,
    })
    return g.compile()


def run_agent(user_request, driver_id=None):
    """Run the agent on a request."""
    graph = build_graph()
    state = {
        "user_request": user_request,
        "driver_id": driver_id or "",
        "history": _MEMORY.setdefault("history", []),
    }
    turns = 0
    while turns < MAX_TURNS:
        turns += 1
        state = graph.invoke(state)
        if state.get("next") == "done":
            break
    remember("history", state.get("history", []))
    return state.get("output", "No output")


if __name__ == "__main__":
    request = sys.argv[1] if len(sys.argv) > 1 else "Review driver D-1042"
    print(run_agent(request, driver_id="D-1042"))
