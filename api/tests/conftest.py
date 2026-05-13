"""Shared pytest fixtures for API tests."""

import os
import sys
from pathlib import Path

# Ensure HORIZON_TESTING is set BEFORE horizon_api imports happen so the DB
# pool init is skipped in test context.
os.environ.setdefault("HORIZON_TESTING", "1")

API_ROOT = Path(__file__).resolve().parent.parent
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))
