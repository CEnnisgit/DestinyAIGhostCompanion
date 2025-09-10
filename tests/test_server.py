from fastapi.testclient import TestClient

from server import app


def test_root_endpoint():
    client = TestClient(app)
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"detail": "Send POST /chat with {'message': ...}"}

