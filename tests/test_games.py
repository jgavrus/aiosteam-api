import asyncio
import datetime

import pytest
from aioresponses import CallbackResult, aioresponses

from aiosteam_api import Game, ReleaseDate
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


OWNED_GAME = {  # exactly what GetOwnedGames sends per game
    "appid": 379430, "name": "Kingdom Come: Deliverance", "playtime_forever": 9347,
    "img_icon_url": "915ec515", "has_community_visible_stats": True, "playtime_windows_forever": 9339,
    "playtime_mac_forever": 0, "playtime_linux_forever": 7, "playtime_deck_forever": 0,
    "rtime_last_played": 1780432847, "content_descriptorids": [1, 5], "playtime_disconnected": 0,
}

STORE_DETAILS = {  # a trimmed appdetails payload, keys and shapes as the store sends them
    "type": "game", "name": "ELDEN RING", "steam_appid": 1245620, "required_age": "16", "is_free": False,
    "controller_support": "full", "dlc": [2778580],
    "supported_languages": "English<strong>*</strong>, French<br><strong>*</strong>languages with full "
                           "audio support",
    "developers": ["FromSoftware, Inc."], "publishers": ["FromSoftware, Inc.", "Bandai Namco Entertainment"],
    "price_overview": {"currency": "UAH", "initial": 179900, "final": 143920, "discount_percent": 20,
                       "initial_formatted": "1 799₴", "final_formatted": "1 439₴"},
    "packages": [440408, 1010505], "platforms": {"windows": True, "mac": False, "linux": False},
    "metacritic": {"score": 94, "url": "https://www.metacritic.com/game/pc/elden-ring"},
    "categories": [{"id": 2, "description": "Single-player"}],
    "genres": [{"id": "1", "description": "Action"}, {"id": "3", "description": "RPG"}],
    "recommendations": {"total": 828223},
    "achievements": {"total": 42, "highlighted": [{"name": "Elden Ring", "path": "icon.jpg"}]},
    "release_date": {"coming_soon": False, "date": "24 Feb, 2022"},
    "support_info": {"url": "https://www.bandainamcoent.com/support", "email": ""},
    "content_descriptors": {"ids": [2, 5], "notes": None},
    "ratings": {"esrb": {"rating": "m", "descriptors": "Blood and Gore"}},
    "background": "bg.jpg", "screenshots": [{"id": 0, "path_full": "shot.jpg"}],
    "header_image": "header.jpg", "pc_requirements": {"minimum": "win"},
}


def test_owned_game_payload_is_parsed_in_full(client):
    game = Game.model_validate({**OWNED_GAME, "client": client})

    assert game.app_id == 379430
    assert game.playtime_windows_forever == 9339
    assert game.playtime_linux_forever == 7
    assert game.playtime_deck_forever == 0
    assert game.playtime_disconnected == 0
    assert game.has_community_visible_stats is True
    assert game.content_descriptorids == [1, 5]
    assert game.last_played == datetime.datetime.fromtimestamp(1780432847)


def test_a_game_that_was_never_launched_has_no_last_played(client):
    game = Game(client=client, app_id=105600, name="Terraria")

    assert game.last_played is None
    assert game.unlocked_achievements is None, "nobody has asked for the achievements yet"


def test_apply_app_details_parses_the_whole_store_payload(client):
    game = Game.from_app_details(STORE_DETAILS, client, STEAM_ID)

    assert game.app_id == 1245620 and game.name == "ELDEN RING"
    assert game.type == "game"
    assert game.required_age == 16, "the store sends this as a string"
    assert game.supported_languages == {"English": "full", "French": "text"}
    assert game.price_overview.final == 143920
    assert game.price_overview.final_price == 1439.20
    assert game.price_overview.discount_percent == 20
    assert game.price_overview.final_formatted == "1 439₴"
    assert game.metacritic.score == 94
    assert game.release_date.coming_soon is False
    assert game.release_date.as_date == datetime.date(2022, 2, 24)
    assert [genre.description for genre in game.genres] == ["Action", "RPG"]
    assert [genre.id for genre in game.genres] == [1, 3], "genre ids come as strings"
    assert [category.description for category in game.categories] == ["Single-player"]
    assert game.platforms.windows is True and game.platforms.linux is False
    assert game.achievements.total == 42
    assert game.recommendations.total == 828223
    assert game.developers == ["FromSoftware, Inc."]
    assert len(game.publishers) == 2
    assert game.support_info.url == "https://www.bandainamcoent.com/support"
    assert game.content_descriptors.ids == [2, 5]
    assert game.ratings["esrb"]["rating"] == "m", "every agency has its own shape, so this stays raw"
    assert game.packages == [440408, 1010505]
    assert game.screenshots[0]["path_full"] == "shot.jpg"
    assert game.controller_support == "full"
    assert game.background == "bg.jpg"
    assert game.dlc is None, "dlc ids are not games and have to be fetched separately"


def test_apply_app_details_ignores_keys_the_model_does_not_know(client):
    """The store grows keys over time; an unknown one must not blow up the parse"""
    game = Game.from_app_details({**STORE_DETAILS, "some_new_steam_key": [1, 2]}, client)

    assert not hasattr(game, "some_new_steam_key")
    assert game.name == "ELDEN RING"


def test_a_game_with_store_details_is_rebuildable_from_its_dump(client):
    game = Game.from_app_details(STORE_DETAILS, client, STEAM_ID)
    restored = Game.model_validate(game.model_dump())

    assert restored.price_overview.final_formatted == "1 439₴"
    assert restored.release_date.as_date == datetime.date(2022, 2, 24)
    assert restored.platforms.windows is True
    assert [genre.id for genre in restored.genres] == [1, 3]


@pytest.mark.parametrize("value, expected", [
    ("24 Feb, 2022", datetime.date(2022, 2, 24)),
    ("Feb 24, 2022", datetime.date(2022, 2, 24)),
    ("2022", datetime.date(2022, 1, 1)),
    ("Q1 2026", None),
    ("Coming soon", None),
    ("", None),
    (None, None),
])
def test_release_date_as_date(value, expected):
    """Steam's date string is localized and is not always one day, so it stays a string on the model"""
    assert ReleaseDate(date=value).as_date == expected


async def test_get_user_achievements_parses_them(client):
    game = make_game(client)
    payload = {"playerstats": {"gameName": "Terraria", "achievements": [
        {"apiname": "FIRST", "achieved": 1, "unlocktime": 1724462578, "name": "First", "description": "d"},
        {"apiname": "SECOND", "achieved": 0, "unlocktime": 0, "name": "Second"}]}}

    with aioresponses() as mocked:
        mocked.get(ACHIEVEMENTS, payload=payload)
        achievements = await game.get_user_achievements()

    assert [achievement.api_name for achievement in achievements] == ["FIRST", "SECOND"]
    assert achievements[0].achieved is True
    assert achievements[0].unlock_time == 1724462578
    assert achievements[1].achieved is False
    assert achievements[1].description is None, "hidden achievements come without one"
    assert game.unlocked_achievements == 1
    assert game.player_achievements == achievements
    assert game.user_achievements["playerstats"]["gameName"] == "Terraria", "the raw response is kept too"


async def test_achievements_of_a_private_profile_are_empty(client):
    game = make_game(client)

    with aioresponses() as mocked:
        mocked.get(ACHIEVEMENTS, payload={"playerstats": {"error": "Profile is not public", "success": False}})
        assert await game.get_user_achievements() == []

    assert game.unlocked_achievements == 0


async def test_get_info_from_shop_asks_for_the_whole_payload_of_one_store(client):
    """The store's "basic" filter has no price in it, and the price depends on the country"""
    game = make_game(client)

    with aioresponses() as mocked:
        mocked.get(APP_DETAILS, payload=app_details(105600))
        await game.get_info_from_shop(country="UA")

    url = str(next(iter(mocked.requests))[1])
    assert "cc=UA" in url
    assert "filters" not in url


async def test_get_info_from_shop_can_still_be_narrowed(client):
    game = make_game(client)

    with aioresponses() as mocked:
        mocked.get(APP_DETAILS, payload=app_details(105600))
        await game.get_info_from_shop(filters="price_overview")

    assert "filters=price_overview" in str(next(iter(mocked.requests))[1])
