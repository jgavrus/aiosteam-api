# aiosteam-api

Async Python client wrapper for the Steam Web API.

# Get Started

## Installation

`pip install aiosteam-api`

## Create Steam API web "STEAM_API_KEY"'

[Steam API Web "STEAM_API_KEY"](https://steamcommunity.com/dev/api"STEAM_API_KEY")

Follow instructions to get API "STEAM_API_KEY"

# Basic Usage

### Searching for a user

```python
import asyncio
from aiosteam_api import Steam

steam = Steam("STEAM_API_KEY")


async def some_async_foo():
  user = await steam.search_user("jeygavrus")  # also you can use steam user id for searching


asyncio.run(some_async_foo())
```

it will return User - a pydantic model with additional methods for getting more detail info.   
if you want reformat model to dict use ```user.model_dump()``` method.  
Or ```user.model_dump_json()``` for getting json string.

JSON Response example:

```json
{
  "steam_id": 76561198144619553,
  "player_lvl": null,
  "community_visibility_state": 3,
  "profile_state": 1,
  "persona_name": "stef1k",
  "profile_url": "https://steamcommunity.com/id/jeygavrus/",
  "avatar": {
    "avatar": "https://avatars.steamstatic.com/ba6060e3847fb5571a4c28f0994884d21fbfb1a2.jpg",
    "avatar_medium": "https://avatars.steamstatic.com/ba6060e3847fb5571a4c28f0994884d21fbfb1a2_medium.jpg",
    "avatar_full": "https://avatars.steamstatic.com/ba6060e3847fb5571a4c28f0994884d21fbfb1a2_full.jpg",
    "avatar_hash": "ba6060e3847fb5571a4c28f0994884d21fbfb1a2"
  },
  "last_logoff": 1724462578,
  "persona_state": 0,
  "real_name": "Євгеній",
  "primary_clan_id": 103582791429521408,
  "time_created": 1405203743,
  "persona_state_flags": 0,
  "loc_country_code": "UA",
  "loc_state_code": "13",
  "loc_city_id": 45621,
  "comment_permission": 1,
  "game_id": null,
  "game_extra_info": null,
  "game_server_ip": null,
  "game_server_steam_id": null,
  "lobby_steam_id": null,
  "friends": null,
  "last_played_games": null,
  "owned_games": null,
  "user_badges": null,
  "bans": null,
  "wishlist": null
}
```

Only `steam_id`, `community_visibility_state`, `persona_name`, `profile_url` and `avatar` are always
there: Steam leaves the rest out of a profile that is private or was never set up, so everything else
may be `None`.

The `game_*` and `lobby_steam_id` fields are only filled while the player is **inside a game right now**,
which is also what `user.is_in_game` answers:

```python
user = await steam.search_user("jeygavrus")
if user.is_in_game:
  print(user.persona_name, "is playing", user.game_extra_info)  # -> "kaine~ is playing Counter-Strike 2"
```

### friends, last_played_games, last_played_games, user_badges

By default, these fields are empty. For getting this info - you should use get_* method

Example:

```python
import asyncio
from aiosteam_api import Steam

steam = Steam("STEAM_API_KEY")


async def some_async_foo():
  user = await steam.search_user("jeygavrus")  # also you can use steam user id for searching
  print(user.owned_games)  # None
  games = await user.get_owned_games()
  print(games)  # dict {int_id : Game}
  print(user.owned_games)  # dict {int_id : Game}


asyncio.run(some_async_foo())
```

Owned games dict example

```json
{
  20920: {
    "app_id": 20920,
    "name": "The Witcher 2: Assassins of Kings Enhanced Edition",
    "playtime_two_weeks": 1015,
    // all time parameters in minutes
    "playtime_forever": 1994,
    "img_icon_url": "62dd5c627664df1bcabc47727c7dcd7ccab353e9"
  }
}
```

### Getting Friends List

the same principe as with games

```python
import asyncio

from aiosteam_api import Steam

steam = Steam("STEAM_API_KEY")


async def some_async_foo():
  user = await steam.search_user("jeygavrus")  # also you can use steam user id for searching
  user_friends = await user.get_user_friends_list()
  print(user_friends)  # list[User]
  print(user.friends)


asyncio.run(some_async_foo())
```

Response

```json
 [
  {
    "steam_id": 123456789,
    "player_lvl": null,
    "community_visibility_state": 3,
    "profile_state": 1,
    "persona_name": "Зеновій Гучок",
    "profile_url": "https://steamcommunity.com/id/123456789/",
    "avatar": {
      "avatar": "https://avatars.steamstatic.com/xxxxx.jpg",
      "avatar_medium": "https://avatars.steamstatic.com/xxxxx_medium.jpg",
      "avatar_full": "https://avatars.steamstatic.com/xxxxx_full.jpg",
      "avatar_hash": "68839dbe297c62958aa507d2a0a87052b209540e"
    },
    "last_logoff": 1724503422,
    "persona_state": 0,
    "real_name": "Denys",
    "primary_clan_id": 123456,
    "time_created": 1423770633,
    "persona_state_flags": 0,
    "loc_country_code": "UA",
    "friends": null,
    "last_played_games": null,
    "owned_games": null,
    "user_badges": null,
    "relationship": "friend",
    "friend_since": 1691321801
  }
]

```

### Reusing one connection

Every call opens its own HTTP session by default. Used as an async context manager, the client keeps a
single session (and its connection pool) alive instead, which matters as soon as you fetch a friends list
or a whole library:

```python
import asyncio

from aiosteam_api import Steam


async def some_async_foo():
  async with Steam("STEAM_API_KEY") as steam:
    user = await steam.search_user("jeygavrus")
    await user.get_all_info()


asyncio.run(some_async_foo())
```

`Steam()` also takes `timeout` (seconds per request, default 10) and `max_concurrency` (how many requests
may be in flight at once, default 8). Requests are retried three times with exponential backoff, and a
429 waits for `Retry-After` when Steam sends it.

### Getting everything at once

`get_all_info()` fills every lazy field of the user (level, badges, recently played, owned games, bans,
friends) and returns the user itself. The calls are issued concurrently.

```python
import asyncio

from aiosteam_api import Steam


async def some_async_foo():
  async with Steam("STEAM_API_KEY") as steam:
    user = await steam.search_user("jeygavrus")
    await user.get_all_info()
    print(user.player_lvl, user.user_badges, len(user.owned_games))


asyncio.run(some_async_foo())
```

Other `User` methods: `get_player_lvl()`, `get_user_badges()`, `get_last_played_games()`,
`get_player_bans()`, `get_steamid(vanity)`.

Friend lists longer than 100 are split into batches automatically, because Steam silently truncates
bigger requests. Pass `enriched=False` to get Steam's raw ids and relationships without fetching the
details of every friend:

```python
friends = await user.get_user_friends_list(enriched=False)
# [{'steamid': '123...', 'relationship': 'friend', 'friend_since': 1691321801}, ...]
```

### Wishlist

```python
wishlist = await user.get_wishlist()  # dict {app_id: WishlistItem}
item = wishlist[105600]
print(item.priority, item.date_added)

game = await item.get_game()  # one extra store request, gives a full Game
```

Steam's wishlist endpoint only returns app ids and when they were added, so a `WishlistItem` is not a
`Game`. An empty dict means the wishlist is empty or the profile hides it.

### Shared games (family library)

This is an undocumented Steam endpoint and it does **not** accept the API key. `access_token` is a
separate token you can read from `https://store.steampowered.com/pointssummary/ajaxgetasyncconfig`
while logged in.

```python
shared = await user.get_shared_games("ACCESS_TOKEN")
# games the user owns themselves are left out unless include_owned=True,
# and family-excluded titles (MMO/MP, delisted) are filtered out
```

### Game details from the store

A `Game` (from `user.owned_games` / `user.last_played_games`) knows how to fetch the rest of itself.

```python
import asyncio

from aiosteam_api import Steam


async def some_async_foo():
  async with Steam("STEAM_API_KEY") as steam:
    user = await steam.search_user("jeygavrus")
    games = await user.get_owned_games()
    game = games[105600]  # games are keyed by app_id
    await game.get_info_from_shop()  # store info: descriptions, requirements, languages, dlc
    print(game.short_description, game.supported_languages)


asyncio.run(some_async_foo())
```

`get_info_from_shop()` copies **the whole appdetails payload** onto the model. The parts with a shape
worth keeping become models of their own:

| Field | Model | Example |
|---|---|---|
| `price_overview` | `PriceOverview` | `.final` is in hundredths (`143920`), `.final_price` is `1439.2`, `.final_formatted` is `"1 439₴"` |
| `release_date` | `ReleaseDate` | `.date` is Steam's own string, `.as_date` is a `datetime.date` or `None` for "Q1 2026" |
| `metacritic` | `Metacritic` | `.score`, `.url` |
| `platforms` | `Platforms` | `.windows`, `.mac`, `.linux` |
| `genres`, `categories` | `list[StoreTag]` | `.id`, `.description` |
| `achievements` | `AppAchievements` | `.total` — how many the app has, not the player's progress |
| `recommendations` | `Recommendations` | `.total` — the review count |
| `support_info` | `SupportInfo` | `.url`, `.email` |
| `content_descriptors` | `ContentDescriptors` | `.ids`, `.notes` |

Plain fields come across as they are: `type`, `is_free`, `required_age`, `controller_support`,
`developers`, `publishers`, `packages`, `package_groups`, `screenshots`, `movies`, `demos`, `ratings`,
`background`, `reviews`, the three `*_requirements`, the descriptions, the images, and `dlc` (a list of
`Game`, fetched concurrently).

`supported_languages` is parsed into a dict, e.g. `{"English": "full", "French": "text"}` — `full` means
full audio support.

Two arguments decide how much is fetched and from which store:

```python
await game.get_info_from_shop(country="UA")               # the whole payload, prices in UAH
await game.get_info_from_shop(filters="price_overview")   # only what you name
```

`country` matters because the store answers with its own currency, and `filters=None` (the default) is
what makes the price, genres, release date and ratings show up at all — Steam's own `"basic"` filter
leaves every one of them out. `WishlistItem.get_game()` takes the same two arguments.

The playtime fields of an owned game are filled by `get_owned_games()`, not by the store: `playtime_forever`
and `playtime_two_weeks` alongside the per-platform `playtime_windows_forever`, `playtime_mac_forever`,
`playtime_linux_forever`, `playtime_deck_forever`, plus `rtime_last_played` (`game.last_played` gives it as
a `datetime`), `playtime_disconnected`, `has_community_visible_stats` and `content_descriptorids`.

### User stats and achievements for a game

Both use the `from_user_id` the game was fetched with, so no steam id is needed.

```python
game = (await user.get_owned_games())[105600]
print(await game.get_user_stats())

achievements = await game.get_user_achievements(language="uk")  # defaults to "en"
print(achievements[0].name, achievements[0].achieved, achievements[0].unlock_time)
print(game.unlocked_achievements, "of", len(achievements))
```

`get_user_achievements()` returns a `list[PlayerAchievement]` and also leaves it on
`game.player_achievements`; the untouched response stays in `game.user_achievements`, which is where
Steam's error message for a private profile ends up. A profile that hides its achievements gives an
empty list rather than an error.

`game.get_all_info()` runs `get_info_from_shop()`, `get_user_achievements()` and `get_user_stats()`
together.

### Searching for games / raw app details

These two do not need a user, so they live on the HTTP client. `search_games` scrapes the store's
search-suggest page; `get_app_details` returns the raw `data` object of the store API.

```python
import asyncio

from aiosteam_api import Steam

steam = Steam("STEAM_API_KEY")

apps = asyncio.run(steam.client.search_games("terr"))
details = asyncio.run(steam.client.get_app_details(105600))  # Terraria
```

`search_games` response:

```json
{
  "apps": [
    {
      "id": [105600],
      "link": "https://store.steampowered.com/app/105600/Terraria/?snr=1_7_15__13",
      "name": "Terraria",
      "img": "https://cdn.akamai.steamstatic.com/steam/apps/105600/capsule_sm_120.jpg?t=1590092560",
      "price": "$9.99"
    }
  ]
}
```

Pass `fetch_discounts=True` to also open every result's store page (concurrently) and add
`has_discount` and `discount` to each entry.

### Workshop files

```python
details = await steam.get_published_file_details([published_file_id])
```

`aiosteam_api.steam_types` has the `PublishedFileQueryType` and `PublishedFileInfoMatchingFileType`
enums that go with it.

### Getting user ban status

```python
import asyncio

from aiosteam_api import Steam


async def some_async_foo():
  async with Steam("STEAM_API_KEY") as steam:
    user = await steam.search_user("jeygavrus")
    bans = await user.get_player_bans()
    print(bans.is_clean, bans.number_of_vac_bans, bans.days_since_last_ban)


asyncio.run(some_async_foo())
```

Returns a `PlayerBans` (also left on `user.bans`), or `None` for an id Steam does not know:

```json
{
  "steam_id": 76561198144619553,
  "community_banned": false,
  "vac_banned": false,
  "number_of_vac_bans": 0,
  "days_since_last_ban": 0,
  "number_of_game_bans": 0,
  "economy_ban": "none"
}
```

`days_since_last_ban` is 0 both for an account that was never banned and for one banned today, so read it
together with the counters — or just use `bans.is_clean`.

# Errors

Everything this library raises derives from `SteamAPIError`:

| Exception | When |
|---|---|
| `NotFound` | the user or app does not exist, is private or is banned |
| `InvalidKey` | Steam answered 401/403 — key missing, wrong, or without access |
| `RateLimited` | Steam answered 429; carries `retry_after` when Steam sends the header |
| `SteamAPIError` | any other API error; carries `status` |

```python
from aiosteam_api import NotFound, RateLimited, SteamAPIError
```

# Development

```bash
pip install -e .[test,style]
pytest
ruff check .
```

The test suite mocks Steam with `aioresponses`, so no API key is needed to run it.
