#!/usr/bin/env bash
# HORIZON deploy from local laptop to OVH VPS.
#
# Runs LOCALLY. SSH/rsync over key-auth.
#
# Usage:
#   ./scripts/deploy.sh                                  # uses defaults
#   SERVER_HOST=hantavirus.software ./scripts/deploy.sh  # override target
#
# Idempotent. Re-run anytime to ship new code.
#
# Pre-requisites:
#   1. server_bootstrap.sh has been run on the VPS
#   2. Your laptop's SSH key is in /home/ubuntu/.ssh/authorized_keys on the VPS
#   3. .env.production exists at /home/ubuntu/horizon/.env.production on the VPS
#      (NOT pushed by this script; you put it there once manually after first deploy)

set -euo pipefail

SERVER_HOST="${SERVER_HOST:-hantavirus.software}"
SERVER_USER="${SERVER_USER:-ubuntu}"
REMOTE_DIR="${REMOTE_DIR:-/home/ubuntu/horizon}"
SSH_OPTS="${SSH_OPTS:-}"

cd "$(dirname "$0")/.."

log() { printf '\n\033[1;34m==>\033[0m %s\n' "$*"; }
warn() { printf '\n\033[1;33m[!]\033[0m %s\n' "$*" >&2; }

# 1. Sanity: project tree
[[ -f docker-compose.prod.yml ]] || { warn "Run from project root"; exit 1; }

# 2. Local web build sanity (optional; the image build does it remotely too,
#    but local build catches type errors before pushing)
log "Type-checking the web bundle locally (skip with NO_TYPECHECK=1)"
if [[ "${NO_TYPECHECK:-0}" != "1" ]]; then
    (cd web && npm run type-check)
fi

# 3. Sync project tree to the server.
#    Uses rsync if available (faster, supports --delete), falls back to
#    tar-over-ssh otherwise (works on plain Git Bash for Windows which
#    typically ships without rsync).
log "syncing project to ${SERVER_USER}@${SERVER_HOST}:${REMOTE_DIR}"
EXCLUDES=(
    '.venv'
    '__pycache__'
    '*.pyc'
    '.pytest_cache'
    '.mypy_cache'
    '.ruff_cache'
    '.coverage'
    'coverage.*'
    '.git'
    'node_modules'
    'web/dist'
    '.claude'
    '.env'
    '.env.production'
    '.env.local'
    '.first_boot_runner.py'
)
if command -v rsync >/dev/null 2>&1; then
    RSYNC_EXCLUDES=()
    for e in "${EXCLUDES[@]}"; do
        # rsync wants trailing slash for directory excludes; we add both forms
        RSYNC_EXCLUDES+=("--exclude=${e}/" "--exclude=${e}")
    done
    rsync -avz --delete "${RSYNC_EXCLUDES[@]}" \
        -e "ssh ${SSH_OPTS}" \
        ./ "${SERVER_USER}@${SERVER_HOST}:${REMOTE_DIR}/"
else
    warn "rsync not found; using tar-over-ssh (no --delete; stale files may remain)"
    TAR_EXCLUDES=()
    for e in "${EXCLUDES[@]}"; do
        TAR_EXCLUDES+=("--exclude=${e}")
    done
    # shellcheck disable=SC2029
    tar -czf - "${TAR_EXCLUDES[@]}" . \
        | ssh ${SSH_OPTS} "${SERVER_USER}@${SERVER_HOST}" \
            "mkdir -p ${REMOTE_DIR} && tar -xzf - -C ${REMOTE_DIR}"
fi

# 4. SSH in and bring the stack up
log "Bringing the stack up on the server"
ssh ${SSH_OPTS} "${SERVER_USER}@${SERVER_HOST}" bash <<EOSSH
set -euo pipefail
cd ${REMOTE_DIR}

if [[ ! -f .env.production ]]; then
    echo "ERROR: .env.production missing on the server."
    echo "Copy .env.production.example, fill in passwords, place at:"
    echo "  ${REMOTE_DIR}/.env.production"
    echo "  chmod 600 .env.production"
    exit 1
fi

echo "==> docker compose build + up"
docker compose -f docker-compose.prod.yml --env-file .env.production up -d --build

echo "==> waiting for services to become healthy"
sleep 10
docker compose -f docker-compose.prod.yml ps

echo "==> tailing api logs for first 20 lines"
docker compose -f docker-compose.prod.yml logs --tail=20 api || true
EOSSH

log "Done. Verify:"
echo "  curl -sI https://hantavirus.software/ | head -1     # expect HTTP/2 200"
echo "  curl -s  https://hantavirus.software/health        # expect {\"status\":\"ok\"...}"
echo ""
echo "If TLS isn't issued yet, run scripts/issue_cert.sh on the server first."
