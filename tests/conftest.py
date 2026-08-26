import re

import pytest

from aiosteam_api import Steam
from aiosteam_api.clients.requests_client import RequestsClient

KEY = "test-key"

SUMMARIES = re.compile(r".*GetPlayerSummaries.*")
FRIEND_LIST = re.compile(r".*GetFriendList.*")
RECENTLY_PLAYED = re.compile(r".*GetRecentlyPlayedGames.*")
OWNED_GAMES = re.compile(r".*GetOwnedGames.*")
STEAM_LEVEL = re.compile(r".*GetSteamLevel.*")
BADGES = re.compile(r".*GetBadges.*")
PLAYER_BANS = re.compile(r".*GetPlayerBans.*")
VANITY_URL = re.compile(r".*ResolveVanityURL.*")
WISHLIST = re.compile(r".*GetWishlist.*")
SHARED_LIBRARY = re.compile(r".*GetSharedLibraryApps.*")
PUBLISHED_FILES = re.compile(r".*IPublishedFileService.*")
ACHIEVEMENTS = re.compile(r".*GetPlayerAchievements.*")
USER_STATS = re.compile(r".*GetUserStatsForGame.*")
APP_DETAILS = re.compile(r".*appdetails.*")
APP_SEARCH = re.compile(r".*search/suggest.*")


def player(steam_id: int, name: str = "stef1k", **overrides) -> dict:
    """A GetPlayerSummaries entry, with Steam's own separator-less key names"""
    data = {
        "steamid": steam_id,
        "communityvisibilitystate": 3,
        "profilestate": 1,
        "personaname": name,
        "profileurl": f"https://steamcommunity.com/id/{steam_id}/",
        "avatar": "a.jpg",
        "avatarmedium": "a_medium.jpg",
        "avatarfull": "a_full.jpg",
        "avatarhash": "deadbeef",
        "lastlogoff": 1724462578,
        "personastate": 0,
        "realname": None,
        "primaryclanid": 103582791429521408,
        "timecreated": 1405203743,
        "personastateflags": 0,
        "loccountrycode": "UA",
    }
    data.update(overrides)
    return data


def summaries(*steam_ids: int) -> dict:
    return {"response": {"players": [player(steam_id) for steam_id in steam_ids]}}


def app_details(app_id: int, **overrides) -> dict:
    """A store appdetails payload, wrapper included"""
    data = {
        "type": "game",
        "name": f"App {app_id}",
        "steam_appid": app_id,
        "required_age": "0",
        "is_free": False,
        "short_description": "short",
        "supported_languages": "English<strong>*</strong>, French<br><strong>*</strong>languages with full "
                               "audio support",
        "header_image": "header.jpg",
        "pc_requirements": {"minimum": "win"},
    }
    data.update(overrides)
    return {str(app_id): {"success": True, "data": data}}


SEARCH_HTML = (
    '<a class="match ds_collapse_flag" data-ds-appid="105600" '
    'href="https://store.steampowered.com/app/105600/Terraria/">'
    '<div class="match_name">Terraria</div>'
    '<div class="match_img"><img src="https://cdn.akamai.steamstatic.com/105600.jpg"></div>'
    '<div class="match_price">$9.99</div></a>'
    '<a class="match ds_collapse_flag" data-ds-appid="409210" '
    'href="https://store.steampowered.com/app/409210/Terraria_OST/">'
    '<div class="match_name">Terraria Soundtrack™</div>'
    '<div class="match_img"><img src="https://cdn.akamai.steamstatic.com/409210.jpg"></div>'
    '<div class="match_price">$4.99</div></a>'
)

DISCOUNTED_PAGE = '<div class="game_purchase_discount_countdown">Offer ends 5 February</div>'
FULL_PRICE_PAGE = '<div class="game_purchase_action">Add to Cart</div>'


@pytest.fixture
def client() -> RequestsClient:
    return RequestsClient(KEY)


@pytest.fixture
def steam() -> Steam:
    return Steam(KEY)


def request_count(mocked, pattern: re.Pattern = None) -> int:
    """How many requests aioresponses recorded, optionally only those matching `pattern`"""
    total = 0
    for (_method, url), calls in mocked.requests.items():
        if pattern is None or pattern.match(str(url)):
            total += len(calls)
    return total


def requested_urls(mocked) -> list[str]:
    return [str(url) for (_method, url) in mocked.requests]
