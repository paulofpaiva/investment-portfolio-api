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


def create_wallet(
    client: TestClient,
    auth_headers: dict[str, str],
    name: str = "Growth Wallet",
) -> dict[str, str | bool]:
    response = client.post("/api/v1/wallets/", json={"name": name}, headers=auth_headers)
    return response.json()


def create_user_and_headers(client: TestClient) -> dict[str, str]:
    credentials = {"email": f"user-{uuid4()}@example.com", "password": "strongpassword123"}
    response = client.post("/api/v1/auth/register", json=credentials)
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def create_wallet_transaction(
    client: TestClient,
    auth_headers: dict[str, str],
    wallet_id: str,
    asset_id: str,
    transaction_type: str = "buy",
    quantity: int = 10,
    price_per_unit: float = 189.50,
):
    return client.post(
        f"/api/v1/wallets/{wallet_id}/transactions",
        json={
            "asset_id": asset_id,
            "transaction_type": transaction_type,
            "quantity": quantity,
            "price_per_unit": price_per_unit,
        },
        headers=auth_headers,
    )


def test_create_buy_transaction_returns_201(
    client: TestClient,
    auth_headers: dict[str, str],
    default_wallet: dict[str, str | bool],
) -> None:
    asset = create_asset(client, auth_headers)

    response = create_wallet_transaction(
        client,
        auth_headers,
        str(default_wallet["id"]),
        asset["id"],
        transaction_type="buy",
    )

    assert response.status_code == 201
    assert response.json()["transaction_type"] == "buy"
    assert response.json()["wallet_id"] == str(default_wallet["id"])


def test_create_sell_transaction_returns_201(
    client: TestClient,
    auth_headers: dict[str, str],
    default_wallet: dict[str, str | bool],
) -> None:
    asset = create_asset(client, auth_headers)
    create_wallet_transaction(client, auth_headers, str(default_wallet["id"]), asset["id"], "buy", 10, 189.50)

    response = create_wallet_transaction(
        client,
        auth_headers,
        str(default_wallet["id"]),
        asset["id"],
        "sell",
        2,
        195.00,
    )

    assert response.status_code == 201
    assert response.json()["transaction_type"] == "sell"


def test_list_wallet_transactions_returns_only_current_wallet_data(
    client: TestClient,
    auth_headers: dict[str, str],
    default_wallet: dict[str, str | bool],
) -> None:
    second_wallet = create_wallet(client, auth_headers, "Income Wallet")
    asset = create_asset(client, auth_headers)

    create_wallet_transaction(client, auth_headers, str(default_wallet["id"]), asset["id"], "buy", 10, 189.50)
    create_wallet_transaction(client, auth_headers, str(second_wallet["id"]), asset["id"], "buy", 5, 200.00)

    response = client.get(
        f"/api/v1/wallets/{default_wallet['id']}/transactions?skip=0&limit=10",
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert len(data["items"]) == 1
    assert data["items"][0]["wallet_id"] == str(default_wallet["id"])


def test_list_wallet_transactions_blocks_other_user_wallet(client: TestClient) -> None:
    first_headers = create_user_and_headers(client)
    second_headers = create_user_and_headers(client)
    second_wallet = client.get("/api/v1/wallets/", headers=second_headers).json()[0]

    response = client.get(
        f"/api/v1/wallets/{second_wallet['id']}/transactions",
        headers=first_headers,
    )

    assert response.status_code == 400
    assert response.json() == {
        "message": "Wallet not found.",
        "error_code": "WALLET_NOT_FOUND",
        "status_code": 400,
    }


def test_filter_wallet_transactions_by_type_returns_filtered_results(
    client: TestClient,
    auth_headers: dict[str, str],
    default_wallet: dict[str, str | bool],
) -> None:
    asset = create_asset(client, auth_headers)
    create_wallet_transaction(client, auth_headers, str(default_wallet["id"]), asset["id"], "buy", 10, 189.50)
    create_wallet_transaction(client, auth_headers, str(default_wallet["id"]), asset["id"], "sell", 2, 195.00)

    response = client.get(
        f"/api/v1/wallets/{default_wallet['id']}/transactions?transaction_type=sell&skip=0&limit=10",
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["transaction_type"] == "sell"


def test_get_wallet_transaction_by_id_returns_200(
    client: TestClient,
    auth_headers: dict[str, str],
    default_wallet: dict[str, str | bool],
) -> None:
    asset = create_asset(client, auth_headers)
    created = create_wallet_transaction(client, auth_headers, str(default_wallet["id"]), asset["id"], "buy", 10, 189.50)
    transaction_id = created.json()["id"]

    response = client.get(
        f"/api/v1/wallets/{default_wallet['id']}/transactions/{transaction_id}",
        headers=auth_headers,
    )

    assert response.status_code == 200
    assert response.json()["id"] == transaction_id


def test_delete_wallet_transaction_returns_204(
    client: TestClient,
    auth_headers: dict[str, str],
    default_wallet: dict[str, str | bool],
) -> None:
    asset = create_asset(client, auth_headers)
    created = create_wallet_transaction(client, auth_headers, str(default_wallet["id"]), asset["id"], "buy", 10, 189.50)
    transaction_id = created.json()["id"]

    response = client.delete(
        f"/api/v1/wallets/{default_wallet['id']}/transactions/{transaction_id}",
        headers=auth_headers,
    )

    assert response.status_code == 204


def test_create_transaction_with_invalid_asset_returns_400(
    client: TestClient,
    auth_headers: dict[str, str],
    default_wallet: dict[str, str | bool],
) -> None:
    response = create_wallet_transaction(
        client,
        auth_headers,
        str(default_wallet["id"]),
        str(uuid4()),
        "buy",
        10,
        189.50,
    )

    assert response.status_code == 400
    assert response.json() == {
        "message": "Asset not found.",
        "error_code": "ASSET_NOT_FOUND",
        "status_code": 400,
    }


def test_cannot_sell_more_than_wallet_position_returns_400(
    client: TestClient,
    auth_headers: dict[str, str],
    default_wallet: dict[str, str | bool],
) -> None:
    second_wallet = create_wallet(client, auth_headers, "Speculative Wallet")
    asset = create_asset(client, auth_headers)
    create_wallet_transaction(client, auth_headers, str(default_wallet["id"]), asset["id"], "buy", 2, 189.50)

    response = create_wallet_transaction(
        client,
        auth_headers,
        str(second_wallet["id"]),
        asset["id"],
        "sell",
        3,
        200.00,
    )

    assert response.status_code == 400
    assert response.json() == {
        "message": "Cannot sell more than the current asset position.",
        "error_code": "INSUFFICIENT_ASSET_POSITION",
        "status_code": 400,
    }


def test_wallet_summary_is_scoped_to_wallet_and_separates_profit_loss(
    client: TestClient,
    auth_headers: dict[str, str],
    default_wallet: dict[str, str | bool],
) -> None:
    second_wallet = create_wallet(client, auth_headers, "Long Term Wallet")
    asset = create_asset(client, auth_headers, ticker="NVDA", current_price=130.00)

    create_wallet_transaction(client, auth_headers, str(default_wallet["id"]), asset["id"], "buy", 10, 100.00)
    create_wallet_transaction(client, auth_headers, str(default_wallet["id"]), asset["id"], "buy", 10, 120.00)
    create_wallet_transaction(client, auth_headers, str(default_wallet["id"]), asset["id"], "sell", 5, 150.00)
    create_wallet_transaction(client, auth_headers, str(second_wallet["id"]), asset["id"], "buy", 1, 130.00)

    response = client.get(f"/api/v1/wallets/{default_wallet['id']}/summary", headers=auth_headers)

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
