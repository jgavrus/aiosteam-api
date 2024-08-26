from typing import Optional

from pydantic import BaseModel, model_validator, ConfigDict

from aiosteam_api.clients.requests_client import RequestsClient
from aiosteam_api.exceptions.api_errors import NotFound
from aiosteam_api.steam_models.badges import Badges
from aiosteam_api.steam_models.games import Game


class UserAvatarModel(BaseModel):
    avatar: str
    avatar_medium: str
    avatar_full: str
    avatar_hash: str


class User(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    steam_id: int
    player_lvl: Optional[int]
    community_visibility_state: int
    profile_state: int
    persona_name: str
    profile_url: str
    avatar: UserAvatarModel
    last_logoff: Optional[int]
    persona_state: int
    real_name: Optional[str]
    primary_clan_id: int
    time_created: int
    persona_state_flags: int
    loc_country_code: Optional[str]
    friends: Optional[list['User']]
    last_played_games: Optional[dict[int, Game]]
    owned_games: Optional[dict[int, Game]]
    user_badges: Optional[Badges]
    relationship: Optional[str]
    friend_since: Optional[int]
    client: RequestsClient

    @model_validator(mode='before')
    def create_avatar_field(cls, inp: dict):
        new_inp = {}
        for field in cls.model_fields:
            replaced = field.replace('_', '')
            value = _value if (_value := inp.get(replaced)) is not None else inp.get(field)
            new_inp[field] = value

        new_inp['avatar'] = inp['avatar'] if isinstance(inp['avatar'], UserAvatarModel) else UserAvatarModel(
            avatar=inp.pop('avatar'), avatar_medium=inp.pop('avatarmedium'), avatar_full=inp.pop('avatarfull'),
            avatar_hash=inp.pop('avatarhash'))

        return new_inp

    @staticmethod
    async def search_user(search: str, client: RequestsClient):
        """Searches for exact match

        Args:
            search (str): steam user. For example 'the12thchairman'
            client (aiosteam_api.Client): aiosteam_api.Client
        """
        search_response = await client.request("get", "/ISteamUser/ResolveVanityURL/v1/",
                                               params={"vanityurl": search})

        if search_response("response")("success") != 1:
            return search_response.get("response", {}).get("message")
        steam_id = search_response.get("response", {}).get("steamid")
        return await User.get_user_details(steam_id, client)

    @staticmethod
    async def get_user_details(steam_id: str or int, client: RequestsClient, single=True):
        """Gets user/player details by async_steam ID

        Args:
            steam_id (str or int): Steam 64 ID
            client (aiosteam_api.Client): aiosteam_api.Client
            single (bool, optional): Gets one player. Defaults to True. When false, steam_id can be a string of steamids and delimited by a ','

        """
        user_response = await client.request("get", "/ISteamUser/GetPlayerSummaries/v2/",
                                             params={"steamids": steam_id})
        if not user_response.get("response", {})["players"]:
            raise NotFound(f'{steam_id} is not found')
        if single:
            return User(client=client, **user_response.get("response", {}).get("players", [None])[0])
        else:
            users = []
            for player in user_response.get("response", {}).get("players", []):
                users.append(User(client=client, **player))
            return users

    async def get_all_info(self):
        await self.get_player_lvl()
        await self.get_user_badges()
        await self.get_last_played_games()
        await self.get_owned_games()
        await self.get_player_bans()
        await self.get_user_friends_list()
        return self

    # await self.get_account_public_info() # not worked on steam side

    async def get_user_friends_list(self) -> list['User']:
        """
        Gets friend list of a user
        """

        friends_list_response = await self.client.request("get", "/ISteamUser/GetFriendList/v1/",
                                                          params={"steamid": self.steam_id})
        self.friends = await self._transform_friends(friends_list_response["friendslist"])
        return self.friends  # noqa this is realy return User object

    async def get_last_played_games(self) -> Optional[dict[int, Game]]:
        """Gets recently played games
        """
        games = {}
        response = await self.client.request("get", "/IPlayerService/GetRecentlyPlayedGames/v1/",
                                             params={"steamid": self.steam_id})
        if response.get("response", {}).get('total_count'):
            for game in response.get("response", {}).games("games", []):
                game.update({"client": self.client, "from_user_id": self.steam_id})
                game_object = Game.model_validate(game)
                games[game_object.app_id] = game_object
        self.last_played_games = games
        return self.last_played_games

    async def get_owned_games(self, include_appinfo=True, include_free_games=True) -> Optional[dict[int, Game]]:
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
        for game in response.get("response", {}).games("games", []):
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
        self.player_lvl = response.get("response", {}).get('player_level', 0)
        return response.get("response", {})

    async def get_user_badges(self) -> Badges:
        """Gets user async_steam badges
        """
        response = await self.client.request("get", "/IPlayerService/GetBadges/v1/",
                                             params={"steamid": self.steam_id})
        badges = Badges.model_validate(response.get("response", {}))
        self.user_badges = badges
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

    async def get_player_bans(self) -> dict:
        """Gets account bans info
        """
        response = await self.client.request("get", "/ISteamUser/GetPlayerBans/v1",
                                             params={"steamids": self.steam_id})
        return response

    async def _transform_friends(self, friends_list: dict) -> list[Optional['User']]:
        friend_steam_ids = {friend["steamid"]: friend for friend in friends_list["friends"]}
        friends = await self.get_user_details(",".join(friend_steam_ids.keys()), self.client, False)

        for f in friends:
            if str(f.steam_id) in set(friend_steam_ids.keys()):
                friend = friend_steam_ids[str(f.steam_id)]
                f.relationship = friend["relationship"]
                f.friend_since = friend["friend_since"]

        return friends

    async def get_steamid(self, vanity: str) -> dict:
        """Get steamid64 from vanity URL

        Args:
            vanity (str): Vanity URL
        """
        response = await self.client.request("get", "/ISteamUser/ResolveVanityURL/v1",
                                             params={"vanityurl": vanity})
        return response.get("response", {})
