from fastapi.testclient import TestClient
from src.api.app import app


def test_health() -> None:
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200 and response.json()["status"] == "ok"


def test_signals_endpoint_after_demo_data() -> None:
    client = TestClient(app)
    assert client.get("/signals").status_code == 200
