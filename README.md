# Framework still in development

# Get Started

## Installation

`pip install aiosteam-api`

## Create Steam API web "STEAM_API_KEY"'

[Steam API Web "STEAM_API_KEY"](https://steamcommunity.com/dev/api"STEAM_API_KEY")

Follow instructions to get API "STEAM_API_KEY"'

# Basic Usage

### Searching for a user

```python
from aiosteam import Steam

steam = Steam("STEAM_API_KEY")

steam.users.search_user("jeygavrus")
```

Response

```json
{
  "player": {
    "steamid": "76561198144619553",
    "communityvisibilitystate": 3,
    "profilestate": 1,
    "personaname": "stef1k",
    "profileurl": "https://steamcommunity.com/id/jeygavrus/",
    "avatar": "https://avatars.steamstatic.com/ba6060e3847fb5571a4c28f0994884d21fbfb1a2.jpg",
    "avatarmedium": "https://avatars.steamstatic.com/ba6060e3847fb5571a4c28f0994884d21fbfb1a2_medium.jpg",
    "avatarfull": "https://avatars.steamstatic.com/ba6060e3847fb5571a4c28f0994884d21fbfb1a2_full.jpg",
    "avatarhash": "ba6060e3847fb5571a4c28f0994884d21fbfb1a2",
    "lastlogoff": 1704764074,
    "personastate": 1,
    "realname": "Євгеній",
    "primaryclanid": "103582791429521408",
    "timecreated": 1405203743,
    "personastateflags": 0,
    "loccountrycode": "UA"
  }
}
```

### Getting User details by steam id

```python
import asyncio

from aiosteam import Steam

steam = Steam("STEAM_API_KEY")

# arguments: steam_id
user = asyncio.run(steam.users.get_user_details("76561198144619553"))
```

Response

```json
{
  "player": {
    "steamid": "76561198144619553",
    "communityvisibilitystate": 3,
    "profilestate": 1,
    "personaname": "stef1k",
    "profileurl": "https://steamcommunity.com/id/jeygavrus/",
    "avatar": "https://avatars.steamstatic.com/ba6060e3847fb5571a4c28f0994884d21fbfb1a2.jpg",
    "avatarmedium": "https://avatars.steamstatic.com/ba6060e3847fb5571a4c28f0994884d21fbfb1a2_medium.jpg",
    "avatarfull": "https://avatars.steamstatic.com/ba6060e3847fb5571a4c28f0994884d21fbfb1a2_full.jpg",
    "avatarhash": "ba6060e3847fb5571a4c28f0994884d21fbfb1a2",
    "lastlogoff": 1704764074,
    "personastate": 1,
    "realname": "Євгеній",
    "primaryclanid": "103582791429521408",
    "timecreated": 1405203743,
    "personastateflags": 0,
    "loccountrycode": "UA"
  }
}
```

### Getting Friends List

```python
import asyncio

from aiosteam import Steam

steam = Steam("STEAM_API_KEY")

# arguments: steam_id
user = asyncio.run(steam.users.get_user_friends_list("76561198995017863"))
```

Response

```json
{
  "friends": [
    {
      "steamid": "76561198164668273",
      "communityvisibilitystate": 3,
      "profilestate": 1,
      "personaname": "ProToType",
      "profileurl": "https://steamcommunity.com/id/bruuitssam/",
      "avatar": "https://avatars.akamai.steamstatic.com/fef49e7fa7e1997310d705b2a6158ff8dc1cdfeb.jpg",
      "avatarmedium": "https://avatars.akamai.steamstatic.com/fef49e7fa7e1997310d705b2a6158ff8dc1cdfeb_medium.jpg",
      "avatarfull": "https://avatars.akamai.steamstatic.com/fef49e7fa7e1997310d705b2a6158ff8dc1cdfeb_full.jpg",
      "avatarhash": "fef49e7fa7e1997310d705b2a6158ff8dc1cdfeb",
      "lastlogoff": 1659791200,
      "personastate": 3,
      "realname": "Samuel chance",
      "primaryclanid": "103582791429521408",
      "timecreated": 1416698360,
      "personastateflags": 0,
      "loccountrycode": "US",
      "relationship": "friend",
      "friend_since": 1634692088
    },
    {
      "steamid": "76561198040366189",
      "communityvisibilitystate": 3,
      "profilestate": 1,
      "personaname": "\u2654 Regular Tetragon",
      "commentpermission": 1,
      "profileurl": "https://steamcommunity.com/id/regulartetragon/",
      "avatar": "https://avatars.akamai.steamstatic.com/85ee384bec86399cc79728cbde046516fa704b23.jpg",
      "avatarmedium": "https://avatars.akamai.steamstatic.com/85ee384bec86399cc79728cbde046516fa704b23_medium.jpg",
      "avatarfull": "https://avatars.akamai.steamstatic.com/85ee384bec86399cc79728cbde046516fa704b23_full.jpg",
      "avatarhash": "85ee384bec86399cc79728cbde046516fa704b23",
      "lastlogoff": 1659834670,
      "personastate": 0,
      "realname": "Vincent Mattingly",
      "primaryclanid": "103582791435763797",
      "timecreated": 1302294837,
      "personastateflags": 0,
      "relationship": "friend",
      "friend_since": 1649989273
    },
    {
      "steamid": "76561198030124562",
      "communityvisibilitystate": 3,
      "profilestate": 1,
      "personaname": "Robz",
      "profileurl": "https://steamcommunity.com/profiles/76561198030124562/",
      "avatar": "https://avatars.akamai.steamstatic.com/fef49e7fa7e1997310d705b2a6158ff8dc1cdfeb.jpg",
      "avatarmedium": "https://avatars.akamai.steamstatic.com/fef49e7fa7e1997310d705b2a6158ff8dc1cdfeb_medium.jpg",
      "avatarfull": "https://avatars.akamai.steamstatic.com/fef49e7fa7e1997310d705b2a6158ff8dc1cdfeb_full.jpg",
      "avatarhash": "fef49e7fa7e1997310d705b2a6158ff8dc1cdfeb",
      "lastlogoff": 1659320144,
      "personastate": 1,
      "primaryclanid": "103582791429521408",
      "timecreated": 1283739538,
      "personastateflags": 0,
      "relationship": "friend",
      "friend_since": 1634692171
    }
  ]
}
```

### Getting Users Recently Played Games

```python
import asyncio

from aiosteam import Steam

steam = Steam("STEAM_API_KEY")

# arguments: steam_id
user = asyncio.run(steam.users.get_user_recently_played_games("76561198144619553"))
```

### Getting User Owned Games

```python
import asyncio

from aiosteam import Steam

steam = Steam("STEAM_API_KEY")

# arguments: steam_id
user = asyncio.run(steam.users.get_owned_games("76561198144619553"))
```

### Getting User Steam Level

```python
import asyncio

from aiosteam import Steam

steam = Steam("STEAM_API_KEY")

# arguments: steam_id
user = asyncio.run(steam.users.get_user_steam_level("76561198144619553"))
```

### Getting User Badges

```python
import asyncio

from aiosteam import Steam

steam = Steam("STEAM_API_KEY")

# arguments: steam_id
user = asyncio.run(steam.users.get_user_badges("76561198144619553"))
```

### Getting Community Badge Progress

```python
import asyncio

from aiosteam import Steam

steam = Steam("STEAM_API_KEY")

# arguments: steam_id, badge_id
user = asyncio.run(steam.users.get_community_badge_progress("<steam_id>", "<badge_id>"))
```

### Getting User Public Account

```python
import asyncio

from aiosteam import Steam

steam = Steam("STEAM_API_KEY")

# arguments: steam_id
user = asyncio.run(steam.users.get_account_public_info("<steam_id>"))
```

### Searching for Games

```python
import asyncio

from aiosteam import Steam

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

from aiosteam import Steam

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

from aiosteam import Steam

steam = Steam("STEAM_API_KEY")

# arguments: steam_id, app_id
user = asyncio.run(steam.apps.get_user_stats("<steam_id>", "<app_id>"))
```

### Getting user app achievements

```python
import asyncio

from aiosteam import Steam

steam = Steam("STEAM_API_KEY")

# arguments: steam_id, app_id
user = asyncio.run(steam.apps.get_user_achievements("<steam_id>", "<app_id>"))
```

### Getting user ban status

```python
import asyncio

from aiosteam import Steam

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
