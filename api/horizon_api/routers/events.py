"""Server-Sent Events stream at /api/v1/stream/events.

Phase 2 implementation: emits a `tick` event every TICK_SECONDS with the
current UTC timestamp. Clients use ticks as the live-pulse signal and
re-fetch /cases + /stats + /clusters on each tick.

Phase 3+ will replace the timer with a Redis pub/sub fanout so the worker
can push true "new_case" events on ingest.
"""

from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncIterator
from datetime import UTC, datetime

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse

router = APIRouter()

TICK_SECONDS = 10


async def _event_stream(request: Request) -> AsyncIterator[bytes]:
    # Initial comment line; helps SSE clients confirm connection.
    yield b": connected\n\n"
    while True:
        if await request.is_disconnected():
            break
        payload = json.dumps(
            {
                "type": "tick",
                "ts": datetime.now(tz=UTC).isoformat(timespec="seconds"),
            }
        )
        yield f"data: {payload}\n\n".encode()
        await asyncio.sleep(TICK_SECONDS)


@router.get(
    "/events",
    summary="Server-Sent Events stream (heartbeat ticks every 10s)",
    responses={
        200: {
            "description": "text/event-stream of JSON-payload events",
            "content": {"text/event-stream": {}},
        }
    },
)
async def stream_events(request: Request) -> StreamingResponse:
    return StreamingResponse(
        _event_stream(request),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",  # disable buffering at reverse proxies
        },
    )
