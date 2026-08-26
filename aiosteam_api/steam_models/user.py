import asyncio
from typing import Optional

from pydantic import BaseModel, model_validator, ConfigDict

from aiosteam_api.clients.requests_client import RequestsClient
from aiosteam_api.constants import STEAM_IDS_PER_REQUEST
from aiosteam_api.exceptions.api_errors import NotFound
from aiosteam_api.steam_models.badges import Badges
from aiosteam_api.steam_models.bans import PlayerBans
from aiosteam_api.steam_models.games import Game
from aiosteam_api.steam_models.wishlist import WishlistItem


class UserAvatarModel(BaseModel):
    avatar: str
    avatar_medium: str
    avatar_full: str
    avatar_hash: str


class User(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    # Only the first six are always in a GetPlayerSummaries entry. Everything below them is left out
    # for a profile that is private or was never set up, so none of it may be required.
    steam_id: int
    community_visibility_state: int
    persona_name: str
    profile_url: str
    avatar: UserAvatarModel
    persona_state: int | None = None
    player_lvl: int | None = None
    profile_state: int | None = None
    last_logoff: int | None = None
    real_name: str | None = None
    primary_clan_id: int | None = None
    time_created: int | None = None
    persona_state_flags: int | None = None
    loc_country_code: str | None = None
    loc_state_code: str | None = None
    loc_city_id: int | None = None
    comment_permission: int | None = None

    # only present while the player is in a game right now
    game_id: int | None = None
    game_extra_info: str | None = None
    game_server_ip: str | None = None
    game_server_steam_id: int | None = None
    lobby_steam_id: int | None = None

    friends: list['User'] | None
    last_played_games: dict[int, Game] | None
    owned_games: dict[int, Game] | None
    user_badges: Badges | None
    bans: PlayerBans | None = None
    wishlist: dict[int, WishlistItem] | None = None
    relationship: str | None
    friend_since: int | None
    client: RequestsClient

    @model_validator(mode='before')
    def create_avatar_field(cls, inp: dict):
        if not isinstance(inp, dict):
            return inp

        new_inp = {}
        for field in cls.model_fields:
            replaced = field.replace('_', '')
            value = _value if (_value := inp.get(replaced)) is not None else inp.get(field)
            new_inp[field] = value

        avatar = inp.get('avatar')
        new_inp['avatar'] = avatar if isinstance(avatar, (UserAvatarModel, dict)) else UserAvatarModel(
            avatar=avatar, avatar_medium=inp.get('avatarmedium'), avatar_full=inp.get('avatarfull'),
            avatar_hash=inp.get('avatarhash'))

        return new_inp

    @property
    def is_in_game(self) -> bool:
        """Whether the player is inside a game right now — `game_extra_info` is its name"""
        return bool(self.game_id or self.game_extra_info)

    @staticmethod
    async def search_user(search: str, client: RequestsClient):
        """Searches for exact match

        Args:
            search (str): steam user. For example 'the12thchairman'
            client (aiosteam_api.Client): aiosteam_api.Client
        """
        search_response = await client.request("get", "/ISteamUser/ResolveVanityURL/v1/",
                                               params={"vanityurl": search})

        if search_response.get("response", {}).get("success") != 1:
            return search_response.get("response", {}).get("message")
        steam_id = search_response.get("response", {}).get("steamid")
        return await User.get_user_details(steam_id, client)

    @staticmethod
    async def get_user_details(steam_id: str | int, client: RequestsClient, single=True):
        """Gets user/player details by async_steam ID

        Args:
            steam_id (str or int): Steam 64 ID
            client (aiosteam_api.Client): aiosteam_api.Client
            single (bool, optional): Gets one player. Defaults to True. When false, steam_id can be a
                string of steamids and delimited by a ','

        Raises NotFound when a single player is asked for and Steam returns nothing, which also happens
        for banned and deleted accounts. Asking for several returns whichever of them Steam knows about,
        so a missing one is silently left out rather than failing the whole batch.
        """
        if single:
            user_response = await client.request("get", "/ISteamUser/GetPlayerSummaries/v2/",
                                                 params={"steamids": steam_id})
            players = User._players_of(user_response)
            if not players:
                raise NotFound(f'{steam_id} is not found')
            return User(client=client, **players[0])

        steam_ids = [str(single_id).strip() for single_id in str(steam_id).split(",") if str(single_id).strip()]
        if not steam_ids:
            return []

        # Steam silently drops everything past the first STEAM_IDS_PER_REQUEST ids of a request
        batches = [steam_ids[start:start + STEAM_IDS_PER_REQUEST]
                   for start in range(0, len(steam_ids), STEAM_IDS_PER_REQUEST)]
        responses = await asyncio.gather(*(
            client.request("get", "/ISteamUser/GetPlayerSummaries/v2/", params={"steamids": ",".join(batch)})
            for batch in batches))

        return [User(client=client, **player) for response in responses for player in User._players_of(response)]

    @staticmethod
    def _players_of(response) -> list[dict]:
        if not isinstance(response, dict):
            return []
        return (response.get("response") or {}).get("players") or []

    async def get_all_info(self):
        await asyncio.gather(
            self.get_player_lvl(),
            self.get_user_badges(),
            self.get_player_bans(),
            self.get_user_friends_list(),
            self._get_games(),
        )
        return self

    async def _get_games(self):
        """Recently played has to be fetched first: get_owned_games copies the two week playtime off it"""
        await self.get_last_played_games()
        await self.get_owned_games()

    # await self.get_account_public_info() # not worked on steam side

    async def get_user_friends_list(self, enriched: bool = True) -> list['User'] | list[dict]:
        """
        Gets friend list of a user

        Args:
            enriched (bool, optional): Defaults to True, which fetches the details of every friend and
                returns User objects. Set to False to get Steam's raw list of ids, relationships and
                friend_since timestamps without the extra requests. `self.friends` is only filled in
                when enriched.
        """

        friends_list_response = await self.client.request("get", "/ISteamUser/GetFriendList/v1/",
                                                          params={"steamid": self.steam_id})
        friends_list = (friends_list_response.get("friendslist") or {}).get("friends") or []
        if not enriched:
            return friends_list

        self.friends = await self._transform_friends(friends_list)
        return self.friends  # noqa this is realy return User object

    async def get_last_played_games(self) -> dict[int, Game] | None:
        """Gets recently played games
        """
        games = {}
        response = await self.client.request("get", "/IPlayerService/GetRecentlyPlayedGames/v1/",
                                             params={"steamid": self.steam_id})
        if response.get("response", {}).get('total_count'):
            for game in response.get("response", {}).get("games", []):
                game.update({"client": self.client, "from_user_id": self.steam_id})
                game_object = Game.model_validate(game)
                games[game_object.app_id] = game_object
        self.last_played_games = games
        return self.last_played_games

    async def get_owned_games(self, include_appinfo=True, include_free_games=True) -> dict[int, Game] | None:
        """Gets all owned games of a user by async_steam id

        Args:
            include_appinfo (bool, optional): Includes app/game info. Defaults to True.
            include_free_games (bool, optional): Includes free games. Defaults to True.
        """
        params = {
            "steamid": self.steam_id,
            "include_appinfo": include_appinfo,
            "include_played_free_games": include_free_games,
        }
        response = await self.client.request("get", "/IPlayerService/GetOwnedGames/v1/", params=params)
        games = {}
        for game in response.get("response", {}).get("games", []):
            game.update({"client": self.client, "from_user_id": self.steam_id})
            owned = Game.model_validate(game)
            games[owned.app_id] = owned

        if self.last_played_games:
            for app_id, game in self.last_played_games.items():
                if games.get(app_id):
                    games[app_id].playtime_two_weeks = game.playtime_two_weeks

        self.owned_games = games
        return self.owned_games

    async def get_player_lvl(self) -> dict:
        """Gets user async_steam level

        """
        response = await self.client.request("get", "/IPlayerService/GetSteamLevel/v1/",
                                             params={"steamid": self.steam_id})
        payload = response.get("response") or {} if isinstance(response, dict) else {}
        self.player_lvl = payload.get('player_level', 0)
        return payload

    async def get_user_badges(self) -> Badges:
        """Gets user async_steam badges
        """
        response = await self.client.request("get", "/IPlayerService/GetBadges/v1/",
                                             params={"steamid": self.steam_id})
        payload = response.get("response") or {} if isinstance(response, dict) else {}
        badges = Badges.model_validate(payload)
        self.user_badges = badges
        # the badge page carries the level too, so a caller that asked for badges needs no second
        # request. GetSteamLevel stays authoritative — it also answers for a profile that hides its
        # badges — so this only fills a level nobody has fetched yet, and never races with it.
        if self.player_lvl is None and badges.player_level is not None:
            self.player_lvl = badges.player_level
        return badges

    # async def get_community_badge_progress(self, badge_id: int or str) -> dict:
    #     """Gets user community badge progress
    #
    #     Args:
    #         badge_id (int): Badge ID
    #     """
    #     response = await self.client.request("get", "/IPlayerService/GetCommunityBadgeProgress/v1",
    #                                            params={"steamid": self.steam_id, "badgeid": badge_id}, )
    #     return response.get("response", {})

    async def get_account_public_info(self) -> dict:
        """Gets account public info"""
        response = await self.client.request("get", "/IGameServersService/GetAccountPublicInfo/v1",
                                             params={"steamid": self.steam_id})
        return response

    async def get_player_bans(self) -> PlayerBans | None:
        """Gets account bans info

        Steam answers with a list of players, which stays empty for an id it does not know — that is
        the only case this returns None.
        """
        response = await self.client.request("get", "/ISteamUser/GetPlayerBans/v1",
                                             params={"steamids": self.steam_id})
        players = (response.get("players") or []) if isinstance(response, dict) else []
        self.bans = PlayerBans.model_validate(players[0]) if players else None
        return self.bans

    async def get_wishlist(self) -> dict[int, WishlistItem]:
        """Gets the user's wishlist, keyed by app id

        Only returns app ids and how the user wishlisted them, not full game info: call get_game() on an
        item for that. An empty dict means the wishlist is empty or the profile hides it.
        """
        response = await self.client.request("get", "/IWishlistService/GetWishlist/v1/",
                                             params={"steamid": self.steam_id})
        items = {}
        if isinstance(response, dict):
            for item in (response.get("response") or {}).get("items") or []:
                item.update({"client": self.client, "from_user_id": self.steam_id})
                wishlist_item = WishlistItem.model_validate(item)
                items[wishlist_item.app_id] = wishlist_item

        self.wishlist = items
        return self.wishlist

    async def get_shared_games(self, access_token: str, include_owned: bool = False) -> dict:
        """Gets the games shared with this user through a family library

        This is an undocumented Steam endpoint and it does not accept the API key: `access_token` is a
        separate token, which can be read from https://store.steampowered.com/pointssummary/ajaxgetasyncconfig
        while logged in.

        Args:
            access_token (str): Steam access token, not the API key
            include_owned (bool, optional): Keeps the games this user owns themselves. Defaults to False.
        """
        # include_own has to be set to get every shared game; despite the name it is not about ownership
        response = await self.client.request("get", "/IFamilyGroupsService/GetSharedLibraryApps/v1", params={
            "steamids": self.steam_id,
            "access_token": access_token,
            "family_groupid": 0,
            "include_own": 1,
            "include_non_games": 0,
            "include_excluded": 0,
            "include_free": 0,
        })
        response = (response.get("response") or {}) if isinstance(response, dict) else {}
        apps = response.get("apps") or []

        if not include_owned:
            apps = [app for app in apps
                    if str(self.steam_id) not in {str(owner) for owner in app.get("owner_steamids") or []}]

        # Family-excluded games (MMO/MP titles, delisted apps) come back even with include_excluded=0
        response["apps"] = [app for app in apps if not app.get("exclude_reason")]
        return response

    async def _transform_friends(self, friends_list: list[dict]) -> list[Optional['User']]:
        friend_steam_ids = {str(friend["steamid"]): friend for friend in friends_list}
        if not friend_steam_ids:
            return []

        friends = await self.get_user_details(",".join(friend_steam_ids.keys()), self.client, False)

        for f in friends:
            if friend := friend_steam_ids.get(str(f.steam_id)):
                f.relationship = friend.get("relationship")
                f.friend_since = friend.get("friend_since")

        return friends

    async def get_steamid(self, vanity: str) -> dict:
        """Get steamid64 from vanity URL

        Args:
            vanity (str): Vanity URL
        """
        response = await self.client.request("get", "/ISteamUser/ResolveVanityURL/v1",
                                             params={"vanityurl": vanity})
        return response.get("response", {})
