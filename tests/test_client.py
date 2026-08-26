import asyncio

import pytest
from aioresponses import CallbackResult, aioresponses

from aiosteam_api.clients.requests_client import RequestsClient
from conftest import (APP_DETAILS, APP_SEARCH, DISCOUNTED_PAGE, FULL_PRICE_PAGE, KEY, SEARCH_HTML, SUMMARIES,
                      app_details, request_count, requested_urls,
                      summaries)

SUMMARIES_PATH = "/ISteamUser/GetPlayerSummaries/v2/"


@pytest.fixture
def spy_sessions(monkeypatch):
    """Records the aiohttp session every request was actually sent on"""
    sessions = []
    original = RequestsClient._send

    async def spy(self, session, *args, **kwargs):
        sessions.append(session)
        return await original(self, session, *args, **kwargs)

    monkeypatch.setattr(RequestsClient, "_send", spy)
    return sessions


async def test_open_shares_one_session_across_requests(client, spy_sessions):
    with aioresponses() as mocked:
        mocked.get(SUMMARIES, payload=summaries(1), repeat=True)

        await client.open()
        await client.request("get", SUMMARIES_PATH, params={"steamids": 1})
        await client.request("get", SUMMARIES_PATH, params={"steamids": 2})
        shared = client._session
        await client.close()

    assert len(spy_sessions) == 2
    assert spy_sessions[0] is spy_sessions[1] is shared
    assert shared.closed, "close() has to close the shared session"
    assert client._session is None


async def test_without_open_every_request_gets_its_own_session(client, spy_sessions):
    with aioresponses() as mocked:
        mocked.get(SUMMARIES, payload=summaries(1), repeat=True)

        await client.request("get", SUMMARIES_PATH, params={"steamids": 1})
        await client.request("get", SUMMARIES_PATH, params={"steamids": 2})

    assert spy_sessions[0] is not spy_sessions[1]
    assert all(session.closed for session in spy_sessions), "throwaway sessions have to be closed again"


async def test_the_api_key_is_sent_with_every_request(client):
    with aioresponses() as mocked:
        mocked.get(SUMMARIES, payload=summaries(1))
        await client.request("get", SUMMARIES_PATH, params={"steamids": 1})

    url = str(next(iter(mocked.requests))[1])
    assert f"key={KEY}" in url and "steamids=1" in url


async def test_max_concurrency_caps_requests_in_flight():
    client = RequestsClient(KEY, max_concurrency=2)
    in_flight = 0
    peak = 0

    async def slow(url, **kwargs):
        nonlocal in_flight, peak
        in_flight += 1
        peak = max(peak, in_flight)
        await asyncio.sleep(0.01)
        in_flight -= 1
        return CallbackResult(status=200, payload=summaries(1))

    with aioresponses() as mocked:
        mocked.get(SUMMARIES, callback=slow, repeat=True)
        await client.open()
        await asyncio.gather(*(client.request("get", SUMMARIES_PATH, params={"steamids": i}) for i in range(6)))
        await client.close()

    assert peak <= 2, f"max_concurrency=2 was exceeded, {peak} requests ran at once"


async def test_get_app_details_unwraps_the_data_object(client):
    with aioresponses() as mocked:
        mocked.get(APP_DETAILS, payload=app_details(105600))
        details = await client.get_app_details(105600)

    assert details["name"] == "App 105600"
    assert details["steam_appid"] == 105600


async def test_get_app_details_returns_empty_when_steam_reports_failure(client):
    with aioresponses() as mocked:
        mocked.get(APP_DETAILS, payload={"105600": {"success": False}})
        assert await client.get_app_details(105600) == {}


async def test_search_games_parses_results(client):
    with aioresponses() as mocked:
        mocked.get(APP_SEARCH, body=SEARCH_HTML, content_type="text/html")
        result = await client.search_games("terraria")

    assert [app["id"] for app in result["apps"]] == [[105600], [409210]]
    assert result["apps"][0]["name"] == "Terraria"
    assert result["apps"][0]["price"] == "$9.99"
    assert result["apps"][0]["img"] == "https://cdn.akamai.steamstatic.com/105600.jpg"
    # the store serves UTF-8 and aiohttp decodes it: non-ascii titles have to survive intact
    assert result["apps"][1]["name"] == "Terraria Soundtrack™"


async def test_search_games_without_discounts_makes_one_request(client):
    with aioresponses() as mocked:
        mocked.get(APP_SEARCH, body=SEARCH_HTML, content_type="text/html")
        await client.search_games("terraria")

    assert request_count(mocked) == 1


async def test_search_games_fetches_discounts_per_result(client):
    with aioresponses() as mocked:
        mocked.get(APP_SEARCH, body=SEARCH_HTML, content_type="text/html")
        mocked.get("https://store.steampowered.com/app/105600/Terraria/", body=DISCOUNTED_PAGE,
                   content_type="text/html")
        mocked.get("https://store.steampowered.com/app/409210/Terraria_OST/", body=FULL_PRICE_PAGE,
                   content_type="text/html")

        result = await client.search_games("terraria", fetch_discounts=True)

    assert result["apps"][0]["has_discount"] is True
    assert result["apps"][0]["discount"] == "Offer ends 5 February"
    assert result["apps"][1]["has_discount"] is False
    assert result["apps"][1]["discount"] is None
    assert request_count(mocked) == 3, "one search plus one store page per result"


async def test_get_app_details_can_ask_for_the_whole_payload(client):
    """filters=None is how the docstring says to get every key, and it must not become a literal None"""
    with aioresponses() as mocked:
        mocked.get(APP_DETAILS, payload=app_details(105600))
        details = await client.get_app_details(105600, filters=None)

    assert details["name"] == "App 105600"
    assert "filters" not in requested_urls(mocked)[0]
