from fastapi.testclient import TestClient


def create_asset_payload(ticker: str = "AAPL") -> dict[str, str | float]:
    return {
        "ticker": ticker,
        "name": "Apple Inc.",
        "asset_type": "stock",
        "current_price": 189.50,
    }


def test_create_asset_returns_201(client: TestClient, auth_headers: dict[str, str]) -> None:
    response = client.post("/api/v1/assets/", json=create_asset_payload(), headers=auth_headers)

    assert response.status_code == 201
    assert response.json()["ticker"] == "AAPL"


def test_list_assets_returns_paginated_response(
    client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    client.post("/api/v1/assets/", json=create_asset_payload("AAPL"), headers=auth_headers)
    client.post("/api/v1/assets/", json=create_asset_payload("MSFT"), headers=auth_headers)

    response = client.get("/api/v1/assets/?skip=0&limit=10", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert data["skip"] == 0
    assert data["limit"] == 10
    assert len(data["items"]) == 2


def test_get_asset_by_id_returns_200(client: TestClient, auth_headers: dict[str, str]) -> None:
    created = client.post("/api/v1/assets/", json=create_asset_payload(), headers=auth_headers)
    asset_id = created.json()["id"]

    response = client.get(f"/api/v1/assets/{asset_id}", headers=auth_headers)

    assert response.status_code == 200
    assert response.json()["id"] == asset_id


def test_update_asset_returns_200(client: TestClient, auth_headers: dict[str, str]) -> None:
    created = client.post("/api/v1/assets/", json=create_asset_payload(), headers=auth_headers)
    asset_id = created.json()["id"]

    response = client.put(
        f"/api/v1/assets/{asset_id}",
        json={"current_price": 200.25},
        headers=auth_headers,
    )

    assert response.status_code == 200
    assert response.json()["current_price"] == "200.25"


def test_delete_asset_returns_204(client: TestClient, auth_headers: dict[str, str]) -> None:
    created = client.post("/api/v1/assets/", json=create_asset_payload(), headers=auth_headers)
    asset_id = created.json()["id"]

    response = client.delete(f"/api/v1/assets/{asset_id}", headers=auth_headers)

    assert response.status_code == 204


def test_delete_asset_with_transactions_returns_400(
    client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    created = client.post("/api/v1/assets/", json=create_asset_payload(), headers=auth_headers)
    asset_id = created.json()["id"]
    client.post(
        "/api/v1/transactions/",
        json={
            "asset_id": asset_id,
            "transaction_type": "buy",
            "quantity": 10,
            "price_per_unit": 189.50,
        },
        headers=auth_headers,
    )

    response = client.delete(f"/api/v1/assets/{asset_id}", headers=auth_headers)

    assert response.status_code == 400
    assert response.json() == {
        "message": "Cannot delete asset with existing transactions.",
        "error_code": "ASSET_HAS_TRANSACTIONS",
        "status_code": 400,
    }


def test_create_duplicate_asset_returns_400(client: TestClient, auth_headers: dict[str, str]) -> None:
    client.post("/api/v1/assets/", json=create_asset_payload(), headers=auth_headers)

    response = client.post("/api/v1/assets/", json=create_asset_payload(), headers=auth_headers)

    assert response.status_code == 400
    assert response.json() == {
        "message": "Asset with this ticker already exists.",
        "error_code": "ASSET_TICKER_EXISTS",
        "status_code": 400,
    }


def test_access_without_token_returns_400(client: TestClient) -> None:
    response = client.get("/api/v1/assets/")

    assert response.status_code == 400
    assert response.json() == {
        "message": "Authentication token is required.",
        "error_code": "AUTH_TOKEN_REQUIRED",
        "status_code": 400,
    }
