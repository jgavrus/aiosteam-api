import asyncio

import pytest
from aioresponses import CallbackResult, aioresponses

from aiosteam_api import Game
from conftest import ACHIEVEMENTS, APP_DETAILS, app_details, request_count

STEAM_ID = 76561198144619553
FULL_AUDIO_NOTE = "<br><strong>*</strong>languages with full audio support"


def make_game(client, app_id=105600, name="Terraria") -> Game:
    return Game(client=client, app_id=app_id, name=name, from_user_id=STEAM_ID)


@pytest.mark.parametrize("text, expected", [
    (f"English<strong>*</strong>, French, German{FULL_AUDIO_NOTE}",
     {"English": "full", "French": "text", "German": "text"}),
    ("English, French", {"English": "text", "French": "text"}),
    (f"Russian<strong>*</strong>{FULL_AUDIO_NOTE}", {"Russian": "full"}),
    ("Spanish - Spain, Portuguese - Brazil", {"Spanish - Spain": "text", "Portuguese - Brazil": "text"}),
    ("", {}),
    (None, {}),
])
def test_parse_supported_languages(text, expected):
    assert Game.parse_supported_languages(text) == expected


def test_parse_supported_languages_keeps_the_last_language_clean():
    """str.strip() used to eat characters instead of the footnote, leaving markup in the name"""
    parsed = Game.parse_supported_languages(f"English, Simplified Chinese<strong>*</strong>{FULL_AUDIO_NOTE}")

    assert parsed == {"English": "text", "Simplified Chinese": "full"}
    assert not any("<" in name or "strong" in name for name in parsed)


@pytest.mark.parametrize("value, expected", [
    (0, 0), (18, 18), ("0", 0), ("18", 18), ("18+", 18), ("", None), (None, None), ("unknown", None),
])
def test_parse_required_age(value, expected):
    assert Game.parse_required_age(value) == expected


def test_normalize_steam_keys_is_idempotent(client):
    """A Game has to be rebuildable from its own dump, not only from Steam's key names"""
    game = Game.model_validate({"client": client, "appid": 105600, "name": "Terraria", "playtime_2weeks": 10})
    restored = Game.model_validate(game.model_dump())

    assert game.app_id == restored.app_id == 105600
    assert game.playtime_two_weeks == restored.playtime_two_weeks == 10


def test_from_app_details_survives_the_dlc_id_list(client):
    """appdetails returns dlc as a list of ints, which does not fit the Game model"""
    details = app_details(105600, dlc=[409210, 1323320])["105600"]["data"]
    game = Game.from_app_details(details, client, STEAM_ID)

    assert game.app_id == 105600
    assert game.name == "App 105600"
    assert game.required_age == 0
    assert game.supported_languages == {"English": "full", "French": "text"}
    assert game.dlc is None, "dlc ids are not games and have to be fetched separately"


async def test_get_info_from_shop_fills_the_game(client):
    game = make_game(client)

    with aioresponses() as mocked:
        mocked.get(APP_DETAILS, payload=app_details(105600))
        await game.get_info_from_shop()

    assert game.short_description == "short"
    assert game.header_image == "header.jpg"
    assert game.is_free is False
    assert game.pc_requirements == {"minimum": "win"}


async def test_get_info_from_shop_fetches_dlc_concurrently(client):
    game = make_game(client)
    in_flight = 0
    peak = 0

    async def details_callback(url, **kwargs):
        nonlocal in_flight, peak
        app_id = int(url.query["appids"])
        if app_id == 105600:
            return CallbackResult(status=200, payload=app_details(105600, dlc=[409210, 1323320]))

        in_flight += 1
        peak = max(peak, in_flight)
        await asyncio.sleep(0.01)  # yields, so a second dlc request can overlap this one
        in_flight -= 1
        return CallbackResult(status=200, payload=app_details(app_id))

    with aioresponses() as mocked:
        mocked.get(APP_DETAILS, callback=details_callback, repeat=True)
        await game.get_info_from_shop()

    assert [dlc.app_id for dlc in game.dlc] == [409210, 1323320]
    assert request_count(mocked) == 3, "the game itself plus one request per dlc"
    assert peak == 2, "the dlc requests have to be issued together, not one after another"


async def test_get_user_achievements_sends_the_language(client):
    game = make_game(client)

    with aioresponses() as mocked:
        mocked.get(ACHIEVEMENTS, payload={"playerstats": {"achievements": []}})
        await game.get_user_achievements(language="uk")

    url = str(next(iter(mocked.requests))[1])
    assert "l=uk" in url
    assert f"steamid={STEAM_ID}" in url
