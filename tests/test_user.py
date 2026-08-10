import pytest
from aioresponses import CallbackResult, aioresponses

from aiosteam_api import NotFound, User
from conftest import (APP_DETAILS, BADGES, FRIEND_LIST, OWNED_GAMES, PLAYER_BANS, RECENTLY_PLAYED, SHARED_LIBRARY,
                      STEAM_LEVEL, SUMMARIES, VANITY_URL, WISHLIST, app_details, player, request_count,
                      requested_urls, summaries)

STEAM_ID = 76561198144619553

BADGES_PAYLOAD = {"response": {"badges": [{"badgeid": 1, "level": 1, "completion_time": 1, "xp": 100,
                                           "scarcity": 10}],
                               "player_xp": 100, "player_level": 5,
                               "player_xp_needed_to_level_up": 20, "player_xp_needed_current_level": 90}}


def batching_callback(seen_batches):
    """Answers GetPlayerSummaries with exactly the ids that were asked for, recording the batch sizes"""

    async def callback(url, **kwargs):
        ids = [int(steam_id) for steam_id in url.query["steamids"].split(",")]
        seen_batches.append(len(ids))
        return CallbackResult(status=200, payload=summaries(*ids))

    return callback


async def make_user(client) -> User:
    with aioresponses() as mocked:
        mocked.get(SUMMARIES, payload=summaries(STEAM_ID))
        return await User.get_user_details(STEAM_ID, client)


async def test_get_user_details_maps_steams_key_names(client):
    user = await make_user(client)

    assert user.steam_id == STEAM_ID
    assert user.persona_name == "stef1k"
    assert user.avatar.avatar_full == "a_full.jpg"
    assert user.loc_country_code == "UA"
    assert user.owned_games is None, "relationship fields stay empty until they are asked for"


async def test_get_user_details_raises_not_found_for_a_missing_or_banned_player(client):
    for payload in ({"response": {"players": []}}, {"response": {}}, {}):
        with aioresponses() as mocked:
            mocked.get(SUMMARIES, payload=payload)
            with pytest.raises(NotFound):
                await User.get_user_details(STEAM_ID, client)


async def test_get_user_details_batches_ids_by_hundred(client):
    steam_ids = [str(1000 + i) for i in range(250)]
    batches = []

    with aioresponses() as mocked:
        mocked.get(SUMMARIES, callback=batching_callback(batches), repeat=True)
        users = await User.get_user_details(",".join(steam_ids), client, single=False)

    assert request_count(mocked) == 3, "250 ids have to be split over three requests"
    assert batches == [100, 100, 50]
    assert len(users) == 250


async def test_get_user_details_returns_empty_list_for_no_ids(client):
    assert await User.get_user_details("", client, single=False) == []


async def test_enriched_friends_list_returns_users_with_relationship(client):
    user = await make_user(client)
    friends = [{"steamid": "1001", "relationship": "friend", "friend_since": 1691321801},
               {"steamid": "1002", "relationship": "friend", "friend_since": 1691321802}]

    with aioresponses() as mocked:
        mocked.get(FRIEND_LIST, payload={"friendslist": {"friends": friends}})
        mocked.get(SUMMARIES, callback=batching_callback([]), repeat=True)
        result = await user.get_user_friends_list()

    assert [friend.steam_id for friend in result] == [1001, 1002]
    assert result[0].friend_since == 1691321801
    assert all(friend.relationship == "friend" for friend in result)
    assert user.friends == result


async def test_flat_friends_list_skips_the_details_request(client):
    user = await make_user(client)
    friends = [{"steamid": "1001", "relationship": "friend", "friend_since": 1691321801}]

    with aioresponses() as mocked:
        mocked.get(FRIEND_LIST, payload={"friendslist": {"friends": friends}})
        result = await user.get_user_friends_list(enriched=False)

    assert result == friends
    assert request_count(mocked) == 1, "enriched=False must not fetch player summaries"
    assert user.friends is None


async def test_friends_list_of_a_private_profile_is_empty(client):
    user = await make_user(client)

    with aioresponses() as mocked:
        mocked.get(FRIEND_LIST, payload={})
        assert await user.get_user_friends_list() == []


async def test_owned_games_take_two_week_playtime_from_recently_played(client):
    user = await make_user(client)

    with aioresponses() as mocked:
        mocked.get(RECENTLY_PLAYED, payload={"response": {"total_count": 1, "games": [
            {"appid": 20920, "name": "The Witcher 2", "playtime_2weeks": 1015, "playtime_forever": 1994}]}})
        mocked.get(OWNED_GAMES, payload={"response": {"game_count": 2, "games": [
            {"appid": 20920, "name": "The Witcher 2", "playtime_forever": 1994},
            {"appid": 105600, "name": "Terraria", "playtime_forever": 42}]}})

        await user.get_last_played_games()
        owned = await user.get_owned_games()

    assert owned[20920].playtime_two_weeks == 1015
    assert owned[105600].playtime_two_weeks is None


async def test_empty_game_responses_do_not_raise(client):
    user = await make_user(client)

    with aioresponses() as mocked:
        mocked.get(RECENTLY_PLAYED, payload={"response": {"total_count": 0}})
        mocked.get(OWNED_GAMES, payload={"response": {}})

        assert await user.get_last_played_games() == {}
        assert await user.get_owned_games() == {}


async def test_get_all_info_fills_every_lazy_field(client):
    user = await make_user(client)

    with aioresponses() as mocked:
        mocked.get(STEAM_LEVEL, payload={"response": {"player_level": 42}})
        mocked.get(BADGES, payload=BADGES_PAYLOAD)
        mocked.get(PLAYER_BANS, payload={"players": [{"SteamId": str(STEAM_ID), "VACBanned": False}]})
        mocked.get(FRIEND_LIST, payload={"friendslist": {"friends": [
            {"steamid": "1001", "relationship": "friend", "friend_since": 1}]}})
        mocked.get(SUMMARIES, callback=batching_callback([]), repeat=True)
        mocked.get(RECENTLY_PLAYED, payload={"response": {"total_count": 1, "games": [
            {"appid": 20920, "name": "The Witcher 2", "playtime_2weeks": 1015}]}})
        mocked.get(OWNED_GAMES, payload={"response": {"games": [
            {"appid": 20920, "name": "The Witcher 2", "playtime_forever": 1994}]}})

        await user.get_all_info()

    assert user.player_lvl == 42
    assert user.user_badges.player_level == 5
    assert [friend.steam_id for friend in user.friends] == [1001]
    assert user.last_played_games[20920].playtime_two_weeks == 1015
    # proves the two game calls still run in order even though everything else is gathered
    assert user.owned_games[20920].playtime_two_weeks == 1015


async def test_get_wishlist_returns_items_keyed_by_app_id(client):
    user = await make_user(client)

    with aioresponses() as mocked:
        mocked.get(WISHLIST, payload={"response": {"items": [
            {"appid": 105600, "priority": 1, "date_added": 1724462578},
            {"appid": 20920, "priority": 2, "date_added": 1724462579}]}})
        wishlist = await user.get_wishlist()

    assert sorted(wishlist) == [20920, 105600]
    assert wishlist[105600].priority == 1
    assert wishlist[105600].from_user_id == STEAM_ID
    assert user.wishlist == wishlist


async def test_empty_wishlist_is_an_empty_dict(client):
    user = await make_user(client)

    with aioresponses() as mocked:
        mocked.get(WISHLIST, payload={"success": 2})
        assert await user.get_wishlist() == {}


async def test_wishlist_item_can_fetch_its_game(client):
    user = await make_user(client)

    with aioresponses() as mocked:
        mocked.get(WISHLIST, payload={"response": {"items": [{"appid": 105600, "priority": 1}]}})
        wishlist = await user.get_wishlist()

        mocked.get(APP_DETAILS, payload=app_details(105600))
        game = await wishlist[105600].get_game()

    assert game.app_id == 105600
    assert game.name == "App 105600"
    assert game.short_description == "short"
    assert game.from_user_id == STEAM_ID


async def test_shared_games_filters_owned_and_excluded_apps(client):
    user = await make_user(client)
    apps = [
        {"appid": 1, "name": "shared", "owner_steamids": ["999"], "exclude_reason": 0},
        {"appid": 2, "name": "owned by me", "owner_steamids": [str(STEAM_ID)], "exclude_reason": 0},
        {"appid": 3, "name": "family excluded", "owner_steamids": ["999"], "exclude_reason": 3},
    ]

    with aioresponses() as mocked:
        mocked.get(SHARED_LIBRARY, payload={"response": {"apps": apps}})
        shared = await user.get_shared_games("access-token")

    assert [app["appid"] for app in shared["apps"]] == [1]


async def test_shared_games_can_keep_the_users_own_apps(client):
    user = await make_user(client)
    apps = [
        {"appid": 1, "name": "shared", "owner_steamids": ["999"], "exclude_reason": 0},
        {"appid": 2, "name": "owned by me", "owner_steamids": [str(STEAM_ID)], "exclude_reason": 0},
    ]

    with aioresponses() as mocked:
        mocked.get(SHARED_LIBRARY, payload={"response": {"apps": apps}})
        shared = await user.get_shared_games("access-token", include_owned=True)

    assert [app["appid"] for app in shared["apps"]] == [1, 2]


async def test_shared_games_sends_the_zero_valued_parameters(client):
    """clean_dict used to drop anything falsy, which silently broke this endpoint"""
    user = await make_user(client)

    with aioresponses() as mocked:
        mocked.get(SHARED_LIBRARY, payload={"response": {"apps": []}})
        await user.get_shared_games("access-token")

    url = requested_urls(mocked)[0]
    for expected in ("access_token=access-token", "family_groupid=0", "include_own=1", "include_non_games=0",
                     "include_excluded=0", "include_free=0"):
        assert expected in url, f"{expected} is missing from {url}"


async def test_search_user_resolves_a_vanity_url(steam):
    with aioresponses() as mocked:
        mocked.get(VANITY_URL, payload={"response": {"success": 1, "steamid": str(STEAM_ID)}})
        mocked.get(SUMMARIES, payload=summaries(STEAM_ID))
        user = await steam.search_user("jeygavrus")

    assert user.steam_id == STEAM_ID


async def test_user_survives_a_round_trip_through_model_dump(client):
    user = await make_user(client)
    restored = User.model_validate(user.model_dump())

    assert restored.steam_id == user.steam_id
    assert restored.avatar.avatar_hash == "deadbeef"


def test_player_fixture_matches_the_model_fields():
    """Guards the name mangling rule: field.replace('_', '') has to hit Steam's key"""
    payload = player(STEAM_ID)
    for field in ("persona_name", "profile_url", "primary_clan_id", "loc_country_code"):
        assert field.replace("_", "") in payload
