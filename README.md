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
  "friends": null,
  "last_played_games": null,
  "owned_games": null,
  "user_badges": null
}
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

### Getting everything at once

`get_all_info()` fills every lazy field of the user (level, badges, recently played, owned games, bans,
friends) and returns the user itself.

```python
import asyncio

from aiosteam_api import Steam

steam = Steam("STEAM_API_KEY")


async def some_async_foo():
  user = await steam.search_user("jeygavrus")
  await user.get_all_info()
  print(user.player_lvl, user.user_badges, len(user.owned_games))


asyncio.run(some_async_foo())
```

Other `User` methods: `get_player_lvl()`, `get_user_badges()`, `get_last_played_games()`,
`get_player_bans()`, `get_steamid(vanity)`.

### Game details from the store

A `Game` (from `user.owned_games` / `user.last_played_games`) knows how to fetch the rest of itself.

```python
import asyncio

from aiosteam_api import Steam

steam = Steam("STEAM_API_KEY")


async def some_async_foo():
  user = await steam.search_user("jeygavrus")
  games = await user.get_owned_games()
  game = games[105600]  # games are keyed by app_id
  await game.get_info_from_shop()  # store info: descriptions, requirements, languages, dlc
  print(game.short_description, game.supported_languages)


asyncio.run(some_async_foo())
```

`get_info_from_shop()` fills `required_age`, `is_free`, `detailed_description`, `about_the_game`,
`short_description`, `supported_languages`, `header_image`, `capsule_image`, `capsule_imagev5`,
`pc_requirements`, `mac_requirements`, `linux_requirements` and `dlc` (a list of `Game`).

`supported_languages` is parsed into a dict, e.g.
`{"English": "full", "French": "text"}` — `full` means full audio support.

### User stats and achievements for a game

Both use the `from_user_id` the game was fetched with, so no steam id is needed.

```python
import asyncio

from aiosteam_api import Steam

steam = Steam("STEAM_API_KEY")


async def some_async_foo():
  user = await steam.search_user("jeygavrus")
  games = await user.get_owned_games()
  game = games[105600]
  print(await game.get_user_stats())
  print(await game.get_user_achievements())


asyncio.run(some_async_foo())
```

`game.get_all_info()` runs `get_info_from_shop()`, `get_user_achievements()` and `get_user_stats()` together.

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

### Getting user ban status

```python
import asyncio

from aiosteam_api import Steam

steam = Steam("STEAM_API_KEY")


async def some_async_foo():
  user = await steam.search_user("jeygavrus")
  print(await user.get_player_bans())


asyncio.run(some_async_foo())
```

```json
{
  "players": [
    {
      "SteamId": "76561198144619553",
      "CommunityBanned": false,
      "VACBanned": false,
      "NumberOfVACBans": 0,
      "DaysSinceLastBan": 0,
      "NumberOfGameBans": 0,
      "EconomyBan": "none"
    }
  ]
}
```
