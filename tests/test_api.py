import httpx
import pytest
import respx

from app.config import PRICE_GUIDE_URL
from app.services.scryfall import SCRYFALL_API
from tests.test_price_guide import SAMPLE_GUIDE
from tests.test_scryfall import SOL_RING

NAMED_URL = f"{SCRYFALL_API}/cards/named"
WEBHOOK_URL = "https://discord.test/webhook"

SOL_RING_REQUEST = {"name": "Sol Ring", "set_code": "cmm", "target_price": "1.00"}


@pytest.fixture(autouse=True)
def fake_webhook(monkeypatch):
    monkeypatch.setattr("app.services.discord.DISCORD_WEBHOOK_URL", WEBHOOK_URL)


def add_sol_ring(client, target_price="1.00"):
    respx.get(NAMED_URL).mock(return_value=httpx.Response(200, json=SOL_RING))
    return client.post("/watchlist", json={**SOL_RING_REQUEST, "target_price": target_price})


def mock_feed_and_webhook():
    respx.get(PRICE_GUIDE_URL).mock(return_value=httpx.Response(200, json=SAMPLE_GUIDE))
    return respx.post(WEBHOOK_URL).mock(return_value=httpx.Response(204))


# --- POST /watchlist ---


@respx.mock
def test_add_card(client):
    response = add_sol_ring(client)
    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "Sol Ring"
    assert body["set_name"] == "Commander Masters"
    assert body["target_price"] == "1.00"
    assert body["cardmarket_url"].endswith("idProduct=721733")
    assert body["latest_price"] is None


@respx.mock
def test_add_duplicate_card_returns_409(client):
    add_sol_ring(client)
    assert add_sol_ring(client).status_code == 409


@respx.mock
def test_add_unknown_card_returns_404(client):
    respx.get(NAMED_URL).mock(return_value=httpx.Response(404))
    response = client.post("/watchlist", json={**SOL_RING_REQUEST, "name": "Rhystic Study"})
    assert response.status_code == 404


@respx.mock
def test_add_card_when_scryfall_is_down_returns_502(client):
    respx.get(NAMED_URL).mock(return_value=httpx.Response(503))
    assert client.post("/watchlist", json=SOL_RING_REQUEST).status_code == 502


def test_add_card_with_invalid_price_returns_422(client):
    response = client.post("/watchlist", json={**SOL_RING_REQUEST, "target_price": "0"})
    assert response.status_code == 422


# --- DELETE /watchlist/{id} ---


@respx.mock
def test_delete_card(client):
    card_id = add_sol_ring(client).json()["id"]
    assert client.delete(f"/watchlist/{card_id}").status_code == 204
    assert client.get("/watchlist").json() == []


def test_delete_unknown_card_returns_404(client):
    assert client.delete("/watchlist/99").status_code == 404


# --- POST /watchlist/check ---


@respx.mock
def test_check_sends_alert_only_once(client):
    add_sol_ring(client, target_price="1.00")  # low in the feed is 0.48
    webhook = mock_feed_and_webhook()

    first = client.post("/watchlist/check").json()
    assert first["checked"] == 1
    assert first["alerts_sent"] == 1

    second = client.post("/watchlist/check").json()
    assert second["skipped"] == 1
    assert second["alerts_sent"] == 0

    assert webhook.call_count == 1


@respx.mock
def test_check_without_price_drop_sends_no_alert(client):
    add_sol_ring(client, target_price="0.40")  # low 0.48 is above target
    webhook = mock_feed_and_webhook()

    result = client.post("/watchlist/check").json()
    assert result["checked"] == 1
    assert result["alerts_sent"] == 0
    assert webhook.call_count == 0


# --- GET /watchlist/{id}/history ---


@respx.mock
def test_history(client):
    card_id = add_sol_ring(client).json()["id"]
    mock_feed_and_webhook()
    client.post("/watchlist/check")

    history = client.get(f"/watchlist/{card_id}/history").json()
    assert [check["low"] for check in history["checks"]] == ["0.48"]
    assert history["alerts"][0]["price_at_alert"] == "0.48"


def test_history_unknown_card_returns_404(client):
    assert client.get("/watchlist/99/history").status_code == 404