import asyncio

import aiohttp
import pytest
from aioresponses import aioresponses

from aiosteam_api.clients.utils import build_url_with_params, clean_dict, merge_dict, retry, validator
from aiosteam_api.exceptions.api_errors import InvalidKey, RateLimited, SteamAPIError

URL = "https://api.steampowered.com/test"


def test_clean_dict_keeps_falsy_but_meaningful_values():
    cleaned = clean_dict({"include_own": 0, "admin_query": False, "family_groupid": 0, "name": "", "gone": None})

    assert cleaned == {"include_own": 0, "admin_query": "false", "family_groupid": 0, "name": ""}
    assert "gone" not in cleaned


def test_clean_dict_stringifies_list_members():
    assert clean_dict({"ids": [1, 2, 3]}) == {"ids": "1,2,3"}


def test_merge_dict_overrides_left_with_right():
    assert merge_dict({"a": "1", "b": "2"}, {"b": "3"}) == {"a": "1", "b": "3"}


def test_build_url_with_params_puts_key_first():
    assert build_url_with_params(URL, "k", {"steamids": 1}) == f"{URL}?key=k&steamids=1"
    assert build_url_with_params(URL, "k") == f"{URL}?key=k"


async def test_retry_returns_the_awaited_result_not_a_coroutine():
    calls = []

    @retry(times=3, exceptions=(ValueError,), backoff=0)
    async def flaky():
        calls.append(1)
        if len(calls) < 3:
            raise ValueError("boom")
        return "ok"

    assert await flaky() == "ok"
    assert len(calls) == 3


async def test_retry_reraises_the_last_exception_once_attempts_run_out():
    @retry(times=2, exceptions=(ValueError,), backoff=0)
    async def always_fails():
        raise ValueError("always")

    with pytest.raises(ValueError, match="always"):
        await always_fails()


async def test_retry_waits_for_retry_after_on_429(monkeypatch):
    slept = []

    async def fake_sleep(delay):
        slept.append(delay)

    monkeypatch.setattr(asyncio, "sleep", fake_sleep)
    calls = []

    @retry(times=2, exceptions=(ValueError,), backoff=0.5)
    async def limited():
        calls.append(1)
        if len(calls) == 1:
            raise RateLimited("429", retry_after=7)
        return "ok"

    assert await limited() == "ok"
    assert slept == [7]


async def test_validator_maps_status_codes_to_typed_errors():
    cases = [
        (429, RateLimited),
        (401, InvalidKey),
        (403, InvalidKey),
        (500, SteamAPIError),
    ]
    for status, expected in cases:
        with aioresponses() as mocked:
            mocked.get(URL, status=status, body="nope")
            async with aiohttp.ClientSession() as session:
                async with session.get(URL) as response:
                    with pytest.raises(expected):
                        await validator(response)


async def test_validator_reads_retry_after_header():
    with aioresponses() as mocked:
        mocked.get(URL, status=429, body="slow down", headers={"Retry-After": "3"})
        async with aiohttp.ClientSession() as session:
            async with session.get(URL) as response:
                with pytest.raises(RateLimited) as raised:
                    await validator(response)

    assert raised.value.retry_after == 3
    assert raised.value.status == 429


async def test_validator_returns_text_when_the_body_is_not_json():
    with aioresponses() as mocked:
        mocked.get(URL, status=200, body="<a>html</a>", content_type="text/html")
        async with aiohttp.ClientSession() as session:
            async with session.get(URL) as response:
                assert await validator(response) == "<a>html</a>"


async def test_validator_returns_ok_for_an_empty_body():
    with aioresponses() as mocked:
        mocked.get(URL, status=200, body="")
        async with aiohttp.ClientSession() as session:
            async with session.get(URL) as response:
                assert await validator(response) == "OK"


async def test_validator_keeps_an_empty_json_object_a_dict():
    """Steam answers private profiles with {}, and callers .get() their way through the result"""
    with aioresponses() as mocked:
        mocked.get(URL, status=200, payload={})
        async with aiohttp.ClientSession() as session:
            async with session.get(URL) as response:
                assert await validator(response) == {}
