#!/usr/bin/env bash
# Bring up HORIZON local stack.
# First-time: copies .env.example to .env, starts postgres + redis.

set -euo pipefail

cd "$(dirname "$0")/.."

if [ ! -f .env ]; then
    echo "==> creating .env from .env.example"
    cp .env.example .env
fi

# shellcheck disable=SC1091
set -a; source .env; set +a

echo "==> starting postgres + redis"
docker compose up -d postgres redis

echo "==> waiting for postgres healthy"
for _ in $(seq 1 30); do
    if docker compose exec -T postgres pg_isready -U "${POSTGRES_USER:-horizon}" >/dev/null 2>&1; then
        break
    fi
    sleep 1
done

echo "==> waiting for redis healthy"
for _ in $(seq 1 30); do
    if docker compose exec -T redis redis-cli ping >/dev/null 2>&1; then
        break
    fi
    sleep 1
done

echo ""
echo "==> READY"
echo "  Postgres: localhost:5432  (db=${POSTGRES_DB:-horizon}, user=${POSTGRES_USER:-horizon})"
echo "  Redis:    localhost:6379"
echo ""
echo "Next steps (after Phase 1 T-06/T-07 build their Dockerfiles):"
echo "  docker compose --profile app up -d"
echo "  curl http://localhost:8000/health"
echo "  open http://localhost:5173"
