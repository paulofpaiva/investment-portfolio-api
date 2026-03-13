from fastapi.testclient import TestClient


def create_wallet_payload(name: str = "Growth Wallet") -> dict[str, str]:
    return {"name": name}


def create_asset_payload(ticker: str = "AAPL") -> dict[str, str | float]:
    return {
        "ticker": ticker,
        "name": "Apple Inc.",
        "asset_type": "stock",
        "current_price": 189.50,
    }


def test_register_creates_default_wallet(
    client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    response = client.get("/api/v1/wallets/", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "Default"
    assert data[0]["is_default"] is True


def test_create_wallet_returns_201(client: TestClient, auth_headers: dict[str, str]) -> None:
    response = client.post("/api/v1/wallets/", json=create_wallet_payload(), headers=auth_headers)

    assert response.status_code == 201
    assert response.json()["name"] == "Growth Wallet"
    assert response.json()["is_default"] is False


def test_get_wallet_by_id_returns_200(client: TestClient, auth_headers: dict[str, str]) -> None:
    created = client.post("/api/v1/wallets/", json=create_wallet_payload(), headers=auth_headers)
    wallet_id = created.json()["id"]

    response = client.get(f"/api/v1/wallets/{wallet_id}", headers=auth_headers)

    assert response.status_code == 200
    assert response.json()["id"] == wallet_id


def test_update_wallet_returns_200(client: TestClient, auth_headers: dict[str, str]) -> None:
    created = client.post("/api/v1/wallets/", json=create_wallet_payload(), headers=auth_headers)
    wallet_id = created.json()["id"]

    response = client.put(
        f"/api/v1/wallets/{wallet_id}",
        json={"name": "Retirement Wallet"},
        headers=auth_headers,
    )

    assert response.status_code == 200
    assert response.json()["name"] == "Retirement Wallet"


def test_delete_wallet_returns_204(client: TestClient, auth_headers: dict[str, str]) -> None:
    created = client.post("/api/v1/wallets/", json=create_wallet_payload(), headers=auth_headers)
    wallet_id = created.json()["id"]

    response = client.delete(f"/api/v1/wallets/{wallet_id}", headers=auth_headers)

    assert response.status_code == 204


def test_delete_default_wallet_returns_400(
    client: TestClient,
    auth_headers: dict[str, str],
    default_wallet: dict[str, str | bool],
) -> None:
    response = client.delete(f"/api/v1/wallets/{default_wallet['id']}", headers=auth_headers)

    assert response.status_code == 400
    assert response.json() == {
        "message": "Default wallet cannot be deleted.",
        "error_code": "DEFAULT_WALLET_DELETE_FORBIDDEN",
        "status_code": 400,
    }


def test_delete_wallet_with_transactions_returns_400(
    client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    wallet = client.post("/api/v1/wallets/", json=create_wallet_payload(), headers=auth_headers).json()
    asset = client.post("/api/v1/assets/", json=create_asset_payload(), headers=auth_headers).json()
    client.post(
        f"/api/v1/wallets/{wallet['id']}/transactions",
        json={
            "asset_id": asset["id"],
            "transaction_type": "buy",
            "quantity": 10,
            "price_per_unit": 189.50,
        },
        headers=auth_headers,
    )

    response = client.delete(f"/api/v1/wallets/{wallet['id']}", headers=auth_headers)

    assert response.status_code == 400
    assert response.json() == {
        "message": "Cannot delete wallet with existing transactions.",
        "error_code": "WALLET_HAS_TRANSACTIONS",
        "status_code": 400,
    }
