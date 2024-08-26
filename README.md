# api on stable version now, but documentation still updating

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

# updated part over. all info below  is not updated yet

### Searching for Games

```python
import asyncio

from aiosteam_api import Steam

steam = Steam("STEAM_API_KEY")

# arguments: search
user = asyncio.run(steam.apps.search_games("terr"))
```

Response

```json
{
  "apps": [
    {
      "id": 105600,
      "link": "https://store.steampowered.com/app/105600/Terraria/?snr=1_7_15__13",
      "name": "Terraria",
      "img": "https://cdn.akamai.steamstatic.com/steam/apps/105600/capsule_sm_120.jpg?t=1590092560",
      "price": "$9.99"
    },
    {
      "id": 1202130,
      "link": "https://store.steampowered.com/app/1202130/Starship_Troopers_Terran_Command/?snr=1_7_15__13",
      "name": "Starship Troopers: Terran Command",
      "img": "https://cdn.akamai.steamstatic.com/steam/apps/1202130/capsule_sm_120.jpg?t=1657104501",
      "price": "$29.99"
    },
    {
      "id": 1176470,
      "link": "https://store.steampowered.com/app/1176470/Terra_Invicta/?snr=1_7_15__13",
      "name": "Terra Invicta",
      "img": "https://cdn.akamai.steamstatic.com/steam/apps/1176470/capsule_sm_120.jpg?t=1659933796",
      "price": ""
    },
    {
      "id": 1945600,
      "link": "https://store.steampowered.com/app/1945600/The_Riftbreaker_Metal_Terror/?snr=1_7_15__13",
      "name": "The Riftbreaker: Metal Terror",
      "img": "https://cdn.akamai.steamstatic.com/steam/apps/1945600/capsule_sm_120.jpg?t=1659109312",
      "price": "$9.99"
    },
    {
      "id": 285920,
      "link": "https://store.steampowered.com/app/285920/TerraTech/?snr=1_7_15__13",
      "name": "TerraTech",
      "img": "https://cdn.akamai.steamstatic.com/steam/apps/285920/capsule_sm_120.jpg?t=1644900341",
      "price": "$24.99"
    }
  ]
}
```

### App/Game details

#### Parameters:

- `app_id` (int): The unique App ID of the app you want to retrieve details for. For example, 105600 corresponds to "
  Terraria"

- `country` (str): An optional parameter representing the ISO Country Code. The default value is "US."

- `filters` (str): An optional parameter that allows you to specify a list of "STEAM_API_KEY"s to return in the app
  details. If not provided, it defaults to "basic." The available filter options include:

- `basic` (Default): Returns essential information like type, name, steam_appid, required_age, is_free, dlc,
  detailed_description, short_description, about_the_game, supported_languages, header_image, website, pc_requirements,
  mac_requirements, and linux_requirements.

- Optional filters (Specify one or more of these as a comma-separated string):
    - controller_support
    - dlc
    - fullgame
    - legal_notice
    - developers
    - demos
    - price_overview
    - metacritic
    - categories
    - genres
    - screenshots
    - movies
    - recommendations
    - achievements
      Response

```python
import asyncio

from aiosteam_api import Steam

terraria_app_id = 105600
steam = Steam("STEAM_API_KEY")

# arguments: app_id
user = asyncio.run(steam.apps.get_app_details(terraria_app_id))

```

```json
{
  "105600": {
    "success": true,
    "data": {
      "type": "game",
      "name": "Terraria",
      "steam_appid": 105600,
      "required_age": 0,
      "is_free": false,
      "controller_support": "full",
      "dlc": [
        409210,
        1323320
      ],
      "detailed_description": "Dig, Fight, Explore, Build:  The very world is at your fingertips as you fight for survival, fortune, and glory.   Will you delve deep into cavernous expanses in search of treasure and raw materials with which to craft ever-evolving gear, machinery, and aesthetics?   Perhaps you will choose instead to seek out ever-greater foes to test your mettle in combat?   Maybe you will decide to construct your own city to house the host of mysterious allies you may encounter along your travels? <br><br>In the World of Terraria, the choice is yours!<br><br>Blending elements of classic action games with the freedom of sandbox-style creativity, Terraria is a unique gaming experience where both the journey and the destination are completely in the player’s control.   The Terraria adventure is truly as unique as the players themselves!  <br><br>Are you up for the monumental task of exploring, creating, and defending a world of your own?  <br><br>\t\t\t\t\t\t\t<strong> features:</strong><br>\t\t\t\t\t\t\t<ul class=\"bb_ul\"><li>Sandbox Play<br>\t\t\t\t\t\t\t</li><li> Randomly generated worlds<br>\t\t\t\t\t\t\t</li><li>Free Content Updates<br>\t\t\t\t\t\t\t</li></ul>",
      "about_the_game": "Dig, Fight, Explore, Build:  The very world is at your fingertips as you fight for survival, fortune, and glory.   Will you delve deep into cavernous expanses in search of treasure and raw materials with which to craft ever-evolving gear, machinery, and aesthetics?   Perhaps you will choose instead to seek out ever-greater foes to test your mettle in combat?   Maybe you will decide to construct your own city to house the host of mysterious allies you may encounter along your travels? <br><br>In the World of Terraria, the choice is yours!<br><br>Blending elements of classic action games with the freedom of sandbox-style creativity, Terraria is a unique gaming experience where both the journey and the destination are completely in the player’s control.   The Terraria adventure is truly as unique as the players themselves!  <br><br>Are you up for the monumental task of exploring, creating, and defending a world of your own?  <br><br>\t\t\t\t\t\t\t<strong> features:</strong><br>\t\t\t\t\t\t\t<ul class=\"bb_ul\"><li>Sandbox Play<br>\t\t\t\t\t\t\t</li><li> Randomly generated worlds<br>\t\t\t\t\t\t\t</li><li>Free Content Updates<br>\t\t\t\t\t\t\t</li></ul>",
      "short_description": "Dig, fight, explore, build! Nothing is impossible in this action-packed adventure game. Four Pack also available!",
      "supported_languages": "English, French, Italian, German, Spanish - Spain, Polish, Portuguese - Brazil, Russian, Simplified Chinese",
      "header_image": "https://cdn.akamai.steamstatic.com/steam/apps/105600/header.jpg?t=1666290860",
      "capsule_image": "https://cdn.akamai.steamstatic.com/steam/apps/105600/capsule_231x87.jpg?t=1666290860",
      "capsule_imagev5": "https://cdn.akamai.steamstatic.com/steam/apps/105600/capsule_184x69.jpg?t=1666290860",
      "website": "http://www.terraria.org/",
      "pc_requirements": {
        "minimum": "<h2 class=\"bb_tag\"><strong>REQUIRED</strong></h2><ul class=\"bb_ul\"><li><strong>OS: Windows Xp, Vista, 7, 8/8.1, 10</strong> <br>\t\t\t\t\t\t\t\t\t\t</li><li><strong>Processor: 2.0 Ghz</strong> <br>\t\t\t\t\t\t\t\t\t\t</li><li><strong>Memory: 2.5GB</strong><br>\t\t\t\t\t\t\t\t\t\t</li><li><strong>Hard Disk Space: 200MB </strong> \t<br>\t\t\t\t\t\t\t\t\t\t</li><li><strong>Video Card: 128mb Video Memory, capable of Shader Model 2.0+</strong> <br>\t\t\t\t\t\t\t\t\t\t</li><li><strong>DirectX®: 9.0c or Greater</strong> \t<br>\t\t\t\t\t\t\t\t\t</li></ul>",
        "recommended": "<h2 class=\"bb_tag\"><strong>RECOMMENDED</strong></h2><ul class=\"bb_ul\"><li><strong>OS: Windows 7, 8/8.1, 10</strong> <br>\t\t\t\t\t\t\t\t\t\t</li><li><strong>Processor: Dual Core 3.0 Ghz</strong> <br>\t\t\t\t\t\t\t\t\t\t</li><li><strong>Memory: 4GB</strong><br>\t\t\t\t\t\t\t\t\t\t</li><li><strong>Hard Disk Space: 200MB </strong> \t<br>\t\t\t\t\t\t\t\t\t\t</li><li><strong>Video Card: 256mb Video Memory, capable of Shader Model 2.0+</strong> <br>\t\t\t\t\t\t\t\t\t\t</li><li><strong>DirectX®: 9.0c or Greater</strong> \t<br>\t\t\t\t\t\t\t\t\t</li></ul>"
      },
      "mac_requirements": {
        "minimum": "<h2 class=\"bb_tag\"><strong>REQUIRED</strong></h2><ul class=\"bb_ul\"><li><strong>OS: OSX 10.9.5 - 10.11.6</strong> <br>\t\t\t\t\t\t\t\t\t\t</li><li><strong>Processor: 2.0 Ghz</strong> <br>\t\t\t\t\t\t\t\t\t\t</li><li><strong>Memory: 2.5GB</strong><br>\t\t\t\t\t\t\t\t\t\t</li><li><strong>Hard Disk Space: 200MB </strong> \t<br>\t\t\t\t\t\t\t\t\t\t</li><li><strong>Video Card: 128mb Video Memory, capable of OpenGL 3.0+ support (2.1 with ARB extensions acceptable</strong> <br>\t\t\t\t\t\t\t\t\t</li></ul>",
        "recommended": "<h2 class=\"bb_tag\"><strong>RECOMMENDED</strong></h2><ul class=\"bb_ul\"><li><strong>OS: OSX 10.9.5 - 10.11.6</strong> <br>\t\t\t\t\t\t\t\t\t\t</li><li><strong>Processor: Dual Core 3.0 Ghz</strong> <br>\t\t\t\t\t\t\t\t\t\t</li><li><strong>Memory: 4GB</strong><br>\t\t\t\t\t\t\t\t\t\t</li><li><strong>Hard Disk Space: 200MB </strong> \t<br>\t\t\t\t\t\t\t\t\t\t</li><li><strong>Video Card: 256mb Video Memory, capable of OpenGL 3.0+ support (2.1 with ARB extensions acceptable</strong> <br>\t\t\t\t\t\t\t\t\t</li></ul>"
      },
      "linux_requirements": {
        "minimum": "<h2 class=\"bb_tag\"><strong>REQUIRED</strong></h2>LINUX<br><ul class=\"bb_ul\"><li><strong>OS: Ubuntu 14.04 LTS</strong> <br>\t\t\t\t\t\t\t\t\t\t</li><li><strong>Processor: 2.0 Ghz</strong> <br>\t\t\t\t\t\t\t\t\t\t</li><li><strong>Memory: 2.5GB</strong><br>\t\t\t\t\t\t\t\t\t\t</li><li><strong>Hard Disk Space: 200MB </strong> \t<br>\t\t\t\t\t\t\t\t\t\t</li><li><strong>Video Card: 128mb Video Memory, capable of OpenGL 3.0+ support (2.1 with ARB extensions acceptable</strong> <br>\t\t\t\t\t\t\t\t\t</li></ul>",
        "recommended": "<h2 class=\"bb_tag\"><strong>RECOMMENDED</strong></h2>LINUX<br><ul class=\"bb_ul\"><li><strong>OS: Ubuntu 14.04 LTS</strong> <br>\t\t\t\t\t\t\t\t\t\t</li><li><strong>Processor: Dual Core 3.0 Ghz</strong> <br>\t\t\t\t\t\t\t\t\t\t</li><li><strong>Memory: 4GB</strong><br>\t\t\t\t\t\t\t\t\t\t</li><li><strong>Hard Disk Space: 200MB </strong> \t<br>\t\t\t\t\t\t\t\t\t\t</li><li><strong>Video Card: 256mb Video Memory, capable of OpenGL 3.0+ support (2.1 with ARB extensions acceptable</strong> <br>\t\t\t\t\t\t\t\t\t</li></ul>"
      }
    }
  }
}
```

### Getting user app stats

```python
import asyncio

from aiosteam_api import Steam

steam = Steam("STEAM_API_KEY")

# arguments: steam_id, app_id
user = asyncio.run(steam.apps.get_user_stats("<steam_id>", "<app_id>"))
```

### Getting user app achievements

```python
import asyncio

from aiosteam_api import Steam

steam = Steam("STEAM_API_KEY")

# arguments: steam_id, app_id
user = asyncio.run(steam.apps.get_user_achievements("<steam_id>", "<app_id>"))
```

### Getting user ban status

```python
import asyncio

from aiosteam_api import Steam

steam = Steam("STEAM_API_KEY")

# arguments: steam_id
user = asyncio.run(steam.users.get_player_bans("<steam_id>"))
````

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
