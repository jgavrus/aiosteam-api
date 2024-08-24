from typing import Optional, Any

from .requests_client import RequestsClient
from .exceptions.api_errors import NotFound
from .types.badges import Badges
from .types.games import LastPlayedGames, LastPlayedGame, OwnedGames
from .types.user import UserModel, UsersModel, FriendModel


class UsersClient:
    """Steam Users API client"""

    def __init__(self, client: RequestsClient):
        """Constructor for Steam Users class"""
        self.__client = client

    async def search_user(self, search: str):
        """Searches for exact match

        Args:
            search (str): steam user. For example 'the12thchairman'
        """
        search_response = await self.__client.request("get", "/ISteamUser/ResolveVanityURL/v1/",
                                                      params={"vanityurl": search})

        if search_response["response"]["success"] != 1:
            return search_response["response"]["message"]
        steam_id = search_response["response"]["steamid"]
        return await self.get_user_details(steam_id)

    async def get_user_details(self, steam_id: str or int, single=True):
        """Gets user/player details by async_steam ID

        Args:
            steam_id (str or int): Steam 64 ID
            single (bool, optional): Gets one player. Defaults to True. When false, steam_id can be a string of steamids and delimited by a ','

        """
        user_response = await self.__client.request("get", "/ISteamUser/GetPlayerSummaries/v2/",
                                                    params={"steamids": steam_id})
        if not user_response["response"]["players"]:
            raise NotFound(f'{steam_id} is not found')
        if single:
            return User(client=self.__client, **user_response["response"]["players"][0])
        else:
            return UsersModel(users=user_response["response"]["players"]).users


class User(UserModel, UsersClient):
    def __init__(self, client: RequestsClient, **data: Any):
        UserModel.__init__(self, **data)
        UsersClient.__init__(self, client)
        self.__client = client

    async def get_user_friends_list(self) -> list[FriendModel]:
        """
        Gets friend list of a user
        """

        friends_list_response = await self.__client.request("get", "/ISteamUser/GetFriendList/v1/",
                                                            params={"steamid": self.steam_id})
        transform_friends = await self._transform_friends(friends_list_response["friendslist"])
        self.friends = transform_friends
        return self.friends

    async def get_last_played_games(self) -> list[LastPlayedGame]:
        """Gets recently played games
        """
        games = []
        response = await self.__client.request("get", "/IPlayerService/GetRecentlyPlayedGames/v1/",
                                               params={"steamid": self.steam_id})
        if response["response"].get('total_count'):
            games = LastPlayedGames.model_validate(response["response"]['games']).games
            self.last_played_games = games
        return games

    async def get_owned_games(self, include_appinfo=True, includ_free_games=True) -> dict:
        """Gets all owned games of a user by async_steam id

        Args:
            include_appinfo (bool, optional): Includes app/game info. Defaults to True.
            includ_free_games (bool, optional): Includes free games. Defaults to True.
        """
        params = {
            "steamid": self.steam_id,
            "include_appinfo": include_appinfo,
            "include_played_free_games": includ_free_games,
        }
        response = await self.__client.request("get", "/IPlayerService/GetOwnedGames/v1/", params=params)
        owned = OwnedGames.model_validate(response["response"]['games']).games

        if self.last_played_games:
            for app_id, game in self.last_played_games.items():
                if owned.get(app_id):
                    owned[app_id].playtime_two_weeks = game.playtime_two_weeks

        self.owned_games = owned
        return owned

    async def get_user_steam_level(self) -> dict:
        """Gets user async_steam level

        """
        response = await self.__client.request("get", "/IPlayerService/GetSteamLevel/v1/",
                                               params={"steamid": self.steam_id})
        self.player_lvl = response["response"]['player_level']
        return response["response"]

    async def get_user_badges(self) -> Badges:
        """Gets user async_steam badges
        """
        response = await self.__client.request("get", "/IPlayerService/GetBadges/v1/",
                                               params={"steamid": self.steam_id})
        badges = Badges.model_validate(response["response"])
        self.user_badges = badges
        return badges

    # async def get_community_badge_progress(self, badge_id: int or str) -> dict:
    #     """Gets user community badge progress
    #
    #     Args:
    #         badge_id (int): Badge ID
    #     """
    #     response = await self.__client.request("get", "/IPlayerService/GetCommunityBadgeProgress/v1",
    #                                            params={"steamid": self.steam_id, "badgeid": badge_id}, )
    #     return response["response"]

    async def get_account_public_info(self) -> dict:
        """Gets account public info

        """
        response = await self.__client.request("get", "/IGameServersService/GetAccountPublicInfo/v1",
                                               params={"steamid": self.steam_id})
        return response

    async def get_player_bans(self) -> dict:
        """Gets account bans info
        """
        response = await self.__client.request("get", "/ISteamUser/GetPlayerBans/v1",
                                               params={"steamids": self.steam_id})
        return response

    async def _transform_friends(self, friends_list: dict) -> list[Optional[FriendModel]]:
        friend_steam_ids = {friend["steamid"]: friend for friend in friends_list["friends"]}
        friends = await self.get_user_details(",".join(friend_steam_ids.keys()), False)
        result = []

        for f in friends:
            if str(f.steam_id) in set(friend_steam_ids.keys()):
                friend = friend_steam_ids[str(f.steam_id)]
                result.append(
                    FriendModel(**dict(f), relationship=friend["relationship"], friend_since=friend["friend_since"]))

        return result

    async def get_steamid(self, vanity: str) -> dict:
        """Get steamid64 from vanity URL

        Args:
            vanity (str): Vanity URL
        """
        response = await self.__client.request("get", "/ISteamUser/ResolveVanityURL/v1", params={"vanityurl": vanity})
        return response["response"]
