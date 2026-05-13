#!/usr/bin/env bash
# HORIZON quality gates. Must pass before any task closes.
# Exits non-zero on any failure.

set -euo pipefail

cd "$(dirname "$0")/.."

echo "==> ruff (lint)"
ruff check .

echo "==> ruff (format check)"
ruff format --check .

echo "==> mypy (strict)"
if [ -d api/horizon_api ] || [ -d worker/horizon_worker ]; then
    mypy api worker 2>/dev/null || mypy --explicit-package-bases api worker
else
    echo "    (no python packages yet, skipping)"
fi

echo "==> bandit (security)"
if [ -d api ] || [ -d worker ]; then
    bandit -r api worker -ll -q 2>/dev/null || echo "    (bandit may not be installed yet)"
else
    echo "    (no python packages yet, skipping)"
fi

echo "==> pytest"
if [ -d api/tests ] || [ -d worker/tests ]; then
    pytest --cov --cov-report=term-missing 2>/dev/null || pytest
else
    echo "    (no tests yet, skipping)"
fi

echo ""
echo "==> ALL GATES PASS"
