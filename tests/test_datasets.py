"""Dataset API tests."""

from fastapi.testclient import TestClient


def test_datasets_missing_root(client: TestClient) -> None:
    response = client.get("/api/v1/datasets")
    assert response.status_code == 404
    body = response.json()
    assert body["code"] == "bids_root_missing"
    assert "detail" in body


def test_datasets_with_bids(client_with_bids: TestClient) -> None:
    response = client_with_bids.get("/api/v1/datasets")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["subjects"] == ["01"]
