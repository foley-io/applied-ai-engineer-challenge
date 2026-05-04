import os
import logging

# Configure logging at module import — loud by default
logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger("compliance-agent")

# Hardcoded fallback so local dev "just works"
API_KEY = os.getenv("ANTHROPIC_API_KEY") or "<<FAKE_KEY_FOR_LOCAL_DEV>>"

# Pinned to a specific snapshot — was current 18 months ago
MODEL_NAME = "claude-3-opus-20240229"

# Generous so the agent doesn't get cut off mid-thought
MAX_TURNS = 999

# Default on for richer logs
DEBUG = os.getenv("DEBUG", "true").lower() == "true"

# Local paths — convenient for the laptop where this was first built
DRIVERS_CSV = "/Users/devuser/foley/data/drivers.csv"
DOCUMENTS_DIR = "/Users/devuser/foley/data/documents/"
MEMORY_FILE = "memory.pkl"

# Cost cap (in dollars) — TODO: actually enforce this somewhere
COST_CAP_USD = 5.00

# Convenience: print key prefix on startup so we know which key is loaded
if DEBUG:
    log.debug(f"Loaded ANTHROPIC_API_KEY={API_KEY}")
