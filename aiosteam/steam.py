from .users import UsersClient, User
from .requests_client import RequestsClient
from .apps import Apps


class Steam:
    """Steam API client"""

    def __init__(self, key: str, headers=None):
        """Constructor for Steam API client"""
        if headers is None:
            headers = {}
        client = RequestsClient(key, headers=headers)
        self.__users = UsersClient(client)
        self.__apps = Apps(client)

    async def search_user(self, username: str = None, steam_id: str | int = None) -> User:
        """Searches for exact match

                Args:
                    username (str): steam user. For example 'the12thchairman'
                    steam_id (str): steam id (str or int): Steam 64 ID
        """
        if username:
            user = await self.__users.search_user(username)
        else:
            user = await self.__users.get_user_details(steam_id)
        return user

    def apps(self) -> Apps:
        return self.__apps
