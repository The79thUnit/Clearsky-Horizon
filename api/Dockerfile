# HORIZON API
# FastAPI behind uvicorn, single worker for Phase 1 (Gunicorn + workers Phase 2).

FROM python:3.12-slim AS base

# Security: non-root user + DejaVu fonts for Pillow-rendered OG images
# (the /api/v1/og/{slug}.png endpoint looks for DejaVuSans-Bold.ttf;
# falls back to Pillow's default font if absent, but DejaVu renders the
# typography we want).
RUN apt-get update \
    && apt-get install -y --no-install-recommends fonts-dejavu-core \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd --system horizon \
    && useradd --system --gid horizon --shell /bin/false --home /app horizon \
    && mkdir -p /app \
    && chown horizon:horizon /app

WORKDIR /app

COPY --chown=horizon:horizon requirements.txt ./
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

COPY --chown=horizon:horizon horizon_api ./horizon_api

USER horizon
EXPOSE 8000

HEALTHCHECK --interval=10s --timeout=3s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request, sys; sys.exit(0 if urllib.request.urlopen('http://localhost:8000/health', timeout=2).status == 200 else 1)"

# Use shell form so ${WORKERS} is expanded at runtime (docker-compose.prod.yml
# sets WORKERS=4; dev default falls back to 1). uvicorn multi-worker mode
# requires workers > 1 to be set explicitly.
CMD uvicorn horizon_api.main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --log-level info \
    --workers ${WORKERS:-1} \
    --proxy-headers \
    --forwarded-allow-ips='*'
# Note: forwarded-allow-ips='*' is safe here because port 8000 is never
# exposed directly — all traffic arrives exclusively via the nginx reverse
# proxy on the Docker internal network. TrustedHostMiddleware provides an
# additional layer that rejects any request with an unrecognised Host header.
