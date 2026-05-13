"""
Long-running daemon services (websocket streams, not Celery tasks).

Celery is for periodic poll jobs. Things that need a persistent connection
(AIS websockets, future event-streams) live here and run as their own
docker-compose service.
"""
