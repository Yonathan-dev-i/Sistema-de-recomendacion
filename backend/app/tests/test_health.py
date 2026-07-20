"""Test de la Fase 0: el endpoint /health debe responder 200 y estado 'ok'."""
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_check_returns_200_and_ok_status():
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert "app" in body


def test_root_endpoint_returns_200():
    response = client.get("/")
    assert response.status_code == 200
