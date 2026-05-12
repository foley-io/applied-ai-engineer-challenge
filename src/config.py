import os
import logging

from dotenv import load_dotenv

# Load .env so ANTHROPIC_API_KEY etc. are picked up.
load_dotenv()

# Configure logging at module import — loud by default
logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger("compliance-agent")

# Hardcoded fallback so local dev "just works"
API_KEY = os.getenv("ANTHROPIC_API_KEY") or "<<FAKE_KEY_FOR_LOCAL_DEV>>"

# Pinned to a specific snapshot — was current 18 months ago
MODEL_NAME = "claude-sonnet-4-5"

# reduced from 999 to 10 to reduce cost
MAX_TURNS = 10

# Default on for richer logs
DEBUG = os.getenv("DEBUG", "true").lower() == "true"

# Repo-relative paths so the agent runs from any machine.
DRIVERS_CSV = "data/drivers.csv"
DOCUMENTS_DIR = "data/documents/"
MEMORY_FILE = "memory.pkl"

# Cost cap (in dollars) — TODO: actually enforce this somewhere
COST_CAP_USD = 5.00

# Convenience: print key prefix on startup so we know which key is loaded
if DEBUG:
    log.debug(f"Loaded ANTHROPIC_API_KEY={API_KEY}")
