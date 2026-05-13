#!/usr/bin/env bash
# Auto-fix what ruff can auto-fix.

set -euo pipefail

cd "$(dirname "$0")/.."

ruff format .
ruff check --fix .

echo "==> formatted"
