"""Agent memory.

Persists conversation state across sessions so the agent can pick up where it
left off.
"""
import os
import pickle

from src.config import MEMORY_FILE

# Module-level shared store. All sessions read and write here.
_MEMORY = {}


def remember(key, value):
    """Save a value into agent memory."""
    _MEMORY[key] = value
    # Persist after every set so we don't lose state on crash
    with open(MEMORY_FILE, "wb") as f:
        pickle.dump(_MEMORY, f)


def recall(key):
    """Retrieve a value from agent memory."""
    return _MEMORY.get(key)


def load_memory():
    """Hydrate memory from disk on startup."""
    global _MEMORY
    if os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE, "rb") as f:
            _MEMORY = pickle.load(f)


# Hydrate at import — convenient
load_memory()
