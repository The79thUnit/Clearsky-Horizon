"""Shared pytest fixtures for the worker tests."""

import sys
from pathlib import Path

# Add the worker package root to sys.path so 'horizon_worker' imports without install.
WORKER_ROOT = Path(__file__).resolve().parent.parent
if str(WORKER_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKER_ROOT))
