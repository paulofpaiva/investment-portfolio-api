from uuid import uuid4

from fastapi.testclient import TestClient


def create_asset(client: TestClient, auth_headers: dict[str, str], ticker: str = "AAPL") -> dict[str, str]:
    response = client.post(
        "/api/v1/assets/",
        json={
            "ticker": ticker,
            "name": f"{ticker} Asset",
            "asset_type": "stock",
            "current_price": 189.50,
        },
        headers=auth_headers,
    )
    return response.json()


def create_user_and_headers(client: TestClient) -> dict[str, str]:
    credentials = {"email": f"user-{uuid4()}@example.com", "password": "strongpassword123"}
    response = client.post("/api/v1/auth/register", json=credentials)
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_create_buy_transaction_returns_201(client: TestClient, auth_headers: dict[str, str]) -> None:
    asset = create_asset(client, auth_headers)

    response = client.post(
        "/api/v1/transactions/",
        json={
            "asset_id": asset["id"],
            "transaction_type": "buy",
            "quantity": 10,
            "price_per_unit": 189.50,
        },
        headers=auth_headers,
    )

    assert response.status_code == 201
    assert response.json()["transaction_type"] == "buy"


def test_create_sell_transaction_returns_201(client: TestClient, auth_headers: dict[str, str]) -> None:
    asset = create_asset(client, auth_headers)
    client.post(
        "/api/v1/transactions/",
        json={
            "asset_id": asset["id"],
            "transaction_type": "buy",
            "quantity": 10,
            "price_per_unit": 189.50,
        },
        headers=auth_headers,
    )

    response = client.post(
        "/api/v1/transactions/",
        json={
            "asset_id": asset["id"],
            "transaction_type": "sell",
            "quantity": 2,
            "price_per_unit": 195.00,
        },
        headers=auth_headers,
    )

    assert response.status_code == 201
    assert response.json()["transaction_type"] == "sell"


def test_list_transactions_returns_only_current_user_data(client: TestClient) -> None:
    first_headers = create_user_and_headers(client)
    second_headers = create_user_and_headers(client)

    first_asset = create_asset(client, first_headers, "AAPL")
    second_asset = create_asset(client, second_headers, "MSFT")

    client.post(
        "/api/v1/transactions/",
        json={
            "asset_id": first_asset["id"],
            "transaction_type": "buy",
            "quantity": 10,
            "price_per_unit": 189.50,
        },
        headers=first_headers,
    )
    client.post(
        "/api/v1/transactions/",
        json={
            "asset_id": second_asset["id"],
            "transaction_type": "buy",
            "quantity": 5,
            "price_per_unit": 300.00,
        },
        headers=second_headers,
    )

    response = client.get("/api/v1/transactions/?skip=0&limit=10", headers=first_headers)

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert len(data["items"]) == 1
    assert data["items"][0]["asset_ticker"] == "AAPL"


def test_filter_transactions_by_type_returns_filtered_results(
    client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    asset = create_asset(client, auth_headers)
    client.post(
        "/api/v1/transactions/",
        json={
            "asset_id": asset["id"],
            "transaction_type": "buy",
            "quantity": 10,
            "price_per_unit": 189.50,
        },
        headers=auth_headers,
    )
    client.post(
        "/api/v1/transactions/",
        json={
            "asset_id": asset["id"],
            "transaction_type": "sell",
            "quantity": 2,
            "price_per_unit": 195.00,
        },
        headers=auth_headers,
    )

    response = client.get(
        "/api/v1/transactions/?transaction_type=sell&skip=0&limit=10",
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["transaction_type"] == "sell"


def test_delete_transaction_returns_204(client: TestClient, auth_headers: dict[str, str]) -> None:
    asset = create_asset(client, auth_headers)
    created = client.post(
        "/api/v1/transactions/",
        json={
            "asset_id": asset["id"],
            "transaction_type": "buy",
            "quantity": 10,
            "price_per_unit": 189.50,
        },
        headers=auth_headers,
    )
    transaction_id = created.json()["id"]

    response = client.delete(f"/api/v1/transactions/{transaction_id}", headers=auth_headers)

    assert response.status_code == 204


def test_create_transaction_with_invalid_asset_returns_400(
    client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    response = client.post(
        "/api/v1/transactions/",
        json={
            "asset_id": str(uuid4()),
            "transaction_type": "buy",
            "quantity": 10,
            "price_per_unit": 189.50,
        },
        headers=auth_headers,
    )

    assert response.status_code == 400
    assert response.json() == {"message": "Asset not found."}
