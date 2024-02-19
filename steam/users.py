from .client import Client


class Users:
    """Steam Users API client"""

    def __init__(self, client: Client):
        """Constructor for Steam Users class"""
        self.__client = client

    async def search_user(self, search: str) -> dict:
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

    async def get_user_details(self, steam_id: str or int, single=True) -> dict:
        """Gets user/player details by steam ID

        Args:
            steam_id (str or int): Steam 64 ID
            single (bool, optional): Gets one player. Defaults to True. When false, steam_id can be a string of steamids and delimited by a ','

        """
        user_response = await self.__client.request("get", "/ISteamUser/GetPlayerSummaries/v2/",
                                                    params={"steamids": steam_id})
        if single:
            return {"player": user_response["response"]["players"][0]}
        else:
            return {"players": user_response["response"]["players"]}

    async def get_user_friends_list(self, steam_id: str or int) -> dict:
        """Gets friend list of a user

        Args:
            steam_id (str): Steam 64 ID
        """
        friends_list_response = await self.__client.request("get", "/ISteamUser/GetFriendList/v1/",
                                                            params={"steamid": steam_id})
        transform_friends = await self._transform_friends(friends_list_response["friendslist"])
        return {"friends": transform_friends}

    async def get_user_recently_played_games(self, steam_id: str or int) -> dict:
        """Gets recently played games

        Args:
            steam_id (str): Steam 64 ID
        """
        response = await self.__client.request("get", "/IPlayerService/GetRecentlyPlayedGames/v1/",
                                               params={"steamid": steam_id})
        return response["response"]

    async def get_owned_games(self, steam_id: str or int, include_appinfo=True, includ_free_games=True) -> dict:
        """Gets all owned games of a user by steam id

        Args:
            steam_id (str): Steam 64 ID
            include_appinfo (bool, optional): Includes app/game info. Defaults to True.
            includ_free_games (bool, optional): Includes free games. Defaults to True.
        """
        params = {
            "steamid": steam_id,
            "include_appinfo": include_appinfo,
            "include_played_free_games": includ_free_games,
        }
        response = await self.__client.request("get", "/IPlayerService/GetOwnedGames/v1/", params=params)
        return response["response"]

    async def get_user_steam_level(self, steam_id: str or int) -> dict:
        """Gets user steam level

        Args:
            steam_id (str): Steam 64 ID
        """
        response = await self.__client.request("get", "/IPlayerService/GetSteamLevel/v1/", params={"steamid": steam_id})
        return response["response"]

    async def get_user_badges(self, steam_id: str or int) -> dict:
        """Gets user steam badges

        Args:
            steam_id (str): Steam 64 ID
        """
        response = await self.__client.request("get", "/IPlayerService/GetBadges/v1/", params={"steamid": steam_id})
        return response["response"]

    async def get_community_badge_progress(self, steam_id: str or str, badge_id: int or str) -> dict:
        """Gets user community badge progress

        Args:
            steam_id (str): Steam 64 ID
            badge_id (int): Badge ID
        """
        response = await self.__client.request("get", "/IPlayerService/GetCommunityBadgeProgress/v1",
                                               params={"steamid": steam_id, "badgeid": badge_id}, )
        return response["response"]

    async def get_account_public_info(self, steam_id: str) -> dict:
        """Gets account public info

        Args:
            steam_id (str): Steam 64 ID
        """
        response = await self.__client.request("get", "/IGameServersService/GetAccountPublicInfo/v1",
                                               params={"steamid": steam_id})
        return response

    async def get_player_bans(self, steam_id: str or str) -> dict:
        """Gets account bans info

        Args:
            steam_id (int or str): Steam 64 ID
        """
        response = await self.__client.request("get", "/ISteamUser/GetPlayerBans/v1", params={"steamids": steam_id})
        return response

    async def _transform_friends(self, friends_list: dict) -> dict:
        friend_steam_ids = [friend["steamid"] for friend in friends_list["friends"]]
        friends = await self.get_user_details(",".join(friend_steam_ids), False)
        friends = friends["players"]
        for f in friends:
            found = next(
                item
                for item in friends_list["friends"]
                if item["steamid"] == f["steamid"]
            )
            f["relationship"] = found["relationship"]
            f["friend_since"] = found["friend_since"]

        return friends

    async def get_steamid(self, vanity: str) -> dict:
        """Get steamid64 from vanity URL

        Args:
            vanity (str): Vanity URL
        """
        response = await self.__client.request("get", "/ISteamUser/ResolveVanityURL/v1", params={"vanityurl": vanity})
        return response["response"]
