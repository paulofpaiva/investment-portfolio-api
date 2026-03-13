from decimal import Decimal
from uuid import uuid4

from fastapi.testclient import TestClient


def create_asset(
    client: TestClient,
    auth_headers: dict[str, str],
    ticker: str = "AAPL",
    current_price: float = 189.50,
) -> dict[str, str]:
    response = client.post(
        "/api/v1/assets/",
        json={
            "ticker": ticker,
            "name": f"{ticker} Asset",
            "asset_type": "stock",
            "current_price": current_price,
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
    assert response.json() == {
        "message": "Asset not found.",
        "error_code": "ASSET_NOT_FOUND",
        "status_code": 400,
    }


def test_cannot_sell_more_than_current_position_returns_400(
    client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    asset = create_asset(client, auth_headers)
    client.post(
        "/api/v1/transactions/",
        json={
            "asset_id": asset["id"],
            "transaction_type": "buy",
            "quantity": 2,
            "price_per_unit": 189.50,
        },
        headers=auth_headers,
    )

    response = client.post(
        "/api/v1/transactions/",
        json={
            "asset_id": asset["id"],
            "transaction_type": "sell",
            "quantity": 3,
            "price_per_unit": 200.00,
        },
        headers=auth_headers,
    )

    assert response.status_code == 400
    assert response.json() == {
        "message": "Cannot sell more than the current asset position.",
        "error_code": "INSUFFICIENT_ASSET_POSITION",
        "status_code": 400,
    }


def test_portfolio_summary_separates_realized_and_unrealized_profit_loss(
    client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    asset = create_asset(client, auth_headers, ticker="NVDA", current_price=130.00)
    client.post(
        "/api/v1/transactions/",
        json={
            "asset_id": asset["id"],
            "transaction_type": "buy",
            "quantity": 10,
            "price_per_unit": 100.00,
        },
        headers=auth_headers,
    )
    client.post(
        "/api/v1/transactions/",
        json={
            "asset_id": asset["id"],
            "transaction_type": "buy",
            "quantity": 10,
            "price_per_unit": 120.00,
        },
        headers=auth_headers,
    )
    client.post(
        "/api/v1/transactions/",
        json={
            "asset_id": asset["id"],
            "transaction_type": "sell",
            "quantity": 5,
            "price_per_unit": 150.00,
        },
        headers=auth_headers,
    )

    response = client.get("/api/v1/portfolio/summary", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert Decimal(data["total_invested"]) == Decimal("1650.00")
    assert Decimal(data["total_realized_profit_loss"]) == Decimal("200.00")
    assert Decimal(data["total_unrealized_profit_loss"]) == Decimal("300.00")
    assert Decimal(data["total_current_value"]) == Decimal("1950.00")
    assert Decimal(data["total_profit_loss"]) == Decimal("500.00")
    assert len(data["assets"]) == 1
    asset_summary = data["assets"][0]
    assert asset_summary["ticker"] == "NVDA"
    assert Decimal(asset_summary["total_quantity"]) == Decimal("15.00")
    assert Decimal(asset_summary["average_price"]) == Decimal("110.00")
    assert Decimal(asset_summary["current_price"]) == Decimal("130.00")
    assert Decimal(asset_summary["current_value"]) == Decimal("1950.00")
    assert Decimal(asset_summary["realized_profit_loss"]) == Decimal("200.00")
    assert Decimal(asset_summary["unrealized_profit_loss"]) == Decimal("300.00")
    assert Decimal(asset_summary["profit_loss"]) == Decimal("500.00")
    assert Decimal(asset_summary["profit_loss_pct"]) == Decimal("22.72727272727272727272727273")
