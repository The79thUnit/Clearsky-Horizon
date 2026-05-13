#!/usr/bin/env bash
# Just the tests. Faster than check.sh.

set -euo pipefail

cd "$(dirname "$0")/.."

pytest "$@"
