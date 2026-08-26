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


async def test_in_game_fields_are_parsed_from_the_summary(client):
    """Steam only sends these while the player is inside a game, and they used to be dropped"""
    in_game = player(STEAM_ID, gameid="730", gameextrainfo="Counter-Strike 2",
                     gameserverip="1.2.3.4:27015", gameserversteamid="90071992547409920",
                     lobbysteamid="109775240000000000", locstatecode="14", loccityid=12345,
                     commentpermission=1)

    with aioresponses() as mocked:
        mocked.get(SUMMARIES, payload={"response": {"players": [in_game]}})
        user = await User.get_user_details(STEAM_ID, client)

    assert user.game_id == 730
    assert user.game_extra_info == "Counter-Strike 2"
    assert user.game_server_ip == "1.2.3.4:27015"
    assert user.game_server_steam_id == 90071992547409920
    assert user.lobby_steam_id == 109775240000000000
    assert user.loc_state_code == "14"
    assert user.loc_city_id == 12345
    assert user.comment_permission == 1
    assert user.is_in_game


async def test_a_player_outside_a_game_has_no_game_fields(client):
    user = await make_user(client)

    assert user.game_id is None
    assert user.game_extra_info is None
    assert not user.is_in_game


async def test_get_player_bans_returns_a_parsed_record(client):
    user = await make_user(client)

    with aioresponses() as mocked:
        mocked.get(PLAYER_BANS, payload={"players": [{
            "SteamId": str(STEAM_ID), "CommunityBanned": False, "VACBanned": True, "NumberOfVACBans": 2,
            "DaysSinceLastBan": 342, "NumberOfGameBans": 1, "EconomyBan": "none"}]})
        bans = await user.get_player_bans()

    assert bans.steam_id == STEAM_ID
    assert bans.vac_banned is True
    assert bans.number_of_vac_bans == 2
    assert bans.number_of_game_bans == 1
    assert bans.days_since_last_ban == 342
    assert not bans.is_clean
    assert user.bans is bans


async def test_an_account_without_bans_is_clean(client):
    user = await make_user(client)

    with aioresponses() as mocked:
        mocked.get(PLAYER_BANS, payload={"players": [{
            "SteamId": str(STEAM_ID), "CommunityBanned": False, "VACBanned": False, "NumberOfVACBans": 0,
            "DaysSinceLastBan": 0, "NumberOfGameBans": 0, "EconomyBan": "none"}]})
        bans = await user.get_player_bans()

    assert bans.is_clean


async def test_bans_of_an_unknown_id_are_none(client):
    user = await make_user(client)

    with aioresponses() as mocked:
        mocked.get(PLAYER_BANS, payload={"players": []})
        assert await user.get_player_bans() is None


async def test_get_user_badges_fills_the_level_it_already_carries(client):
    user = await make_user(client)

    with aioresponses() as mocked:
        mocked.get(BADGES, payload=BADGES_PAYLOAD)
        badges = await user.get_user_badges()

    assert user.player_lvl == 5, "GetBadges answers with the level, so GetSteamLevel is a second request"
    assert badges.xp_into_current_level == 10
    assert badges.badges[0].badge_id == 1


async def test_badges_of_a_profile_that_hides_them_do_not_raise(client):
    user = await make_user(client)

    with aioresponses() as mocked:
        mocked.get(BADGES, payload={"response": {}})
        badges = await user.get_user_badges()

    assert badges.badges == []
    assert badges.player_level is None
    assert user.player_lvl is None


async def test_game_badges_keep_the_app_they_belong_to(client):
    user = await make_user(client)
    payload = {"response": {"badges": [{"badgeid": 13, "level": 147, "completion_time": 1782653643,
                                        "xp": 379, "scarcity": 13221412, "appid": 379430,
                                        "communityitemid": "1234567", "border_color": 0}]}}

    with aioresponses() as mocked:
        mocked.get(BADGES, payload=payload)
        badges = await user.get_user_badges()

    assert badges.badges[0].app_id == 379430
    assert badges.badges[0].community_item_id == 1234567
    assert badges.badges[0].border_color == 0


async def test_a_private_profile_is_parsed_without_the_fields_steam_leaves_out(client):
    """Steam sends a private profile without timecreated, primaryclanid, realname or profilestate —
    a friend list with one private profile in it used to fail the whole batch"""
    private = {"steamid": str(STEAM_ID), "communityvisibilitystate": 1, "personaname": "hidden",
               "profileurl": f"https://steamcommunity.com/profiles/{STEAM_ID}/", "avatar": "a.jpg",
               "avatarmedium": "a_medium.jpg", "avatarfull": "a_full.jpg", "avatarhash": "deadbeef",
               "personastate": 0}

    with aioresponses() as mocked:
        mocked.get(SUMMARIES, payload={"response": {"players": [private]}})
        user = await User.get_user_details(STEAM_ID, client)

    assert user.persona_name == "hidden"
    assert user.community_visibility_state == 1
    assert user.time_created is None
    assert user.primary_clan_id is None
    assert user.profile_state is None
    assert user.real_name is None
