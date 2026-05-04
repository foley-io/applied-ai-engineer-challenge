"""Skills.

Each skill is a function the agent can use. We don't have a registry yet —
just import what you need.
"""
from src.skills.document_review import review_document
from src.skills.safety_score import compute_score
