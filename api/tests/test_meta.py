"""Meta endpoint smoke tests."""

from fastapi.testclient import TestClient
from horizon_api.main import app


def test_health_returns_ok() -> None:
    with TestClient(app) as client:
        response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert "version" in body


def test_openapi_schema_published() -> None:
    with TestClient(app) as client:
        response = client.get("/api/openapi.json")
    assert response.status_code == 200
    schema = response.json()
    assert schema["info"]["title"] == "HORIZON API"
    assert "/api/v1/cases" in schema["paths"]
    assert "/api/v1/sources" in schema["paths"]
    assert "/api/v1/clusters" in schema["paths"]
    assert "/api/v1/clusters/{cluster_id}" in schema["paths"]
    assert "/api/v1/meta/stats" in schema["paths"]
    assert "/api/v1/stream/events" in schema["paths"]
    assert "/api/v1/meta/events" in schema["paths"]
    assert "/health" in schema["paths"]


def test_security_headers_present() -> None:
    with TestClient(app) as client:
        response = client.get("/health")
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["x-frame-options"] == "DENY"
    assert response.headers["referrer-policy"] == "no-referrer"
