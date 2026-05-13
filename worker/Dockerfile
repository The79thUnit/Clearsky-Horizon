# HORIZON worker
# Celery worker + beat in one process (single-machine local-first stack).

FROM python:3.12-slim AS base

# Security: run as non-root user
RUN groupadd --system horizon \
    && useradd --system --gid horizon --shell /bin/false --home /app horizon \
    && mkdir -p /app \
    && chown horizon:horizon /app

WORKDIR /app

# Layer caching: install dependencies before copying source
COPY --chown=horizon:horizon requirements.txt ./
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

COPY --chown=horizon:horizon horizon_worker ./horizon_worker

USER horizon

# Beat + worker in one process (-B). Fine for Phase 1 single-machine local-first.
CMD ["celery", "-A", "horizon_worker.celery_app", "worker", "-B", "-l", "info", "--concurrency", "2"]
