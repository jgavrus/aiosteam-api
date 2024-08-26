from aiosteam_api.clients.requests_client import RequestsClient
from aiosteam_api.steam_models import User


class Steam:
    """Steam API client"""

    def __init__(self, key: str, headers=None):
        """Constructor for Steam API client"""
        if headers is None:
            headers = {}
        self.client = RequestsClient(key, headers=headers)
        self.__users = User

    async def search_user(self, username: str = None, steam_id: str | int = None) -> User:
        """Searches for exact match

                Args:
                    username (str): steam user. For example 'the12thchairman'
                    steam_id (str): steam id (str or int): Steam 64 ID
        """
        if username:
            user = await self.__users.search_user(username, self.client)
        else:
            user = await self.__users.get_user_details(steam_id, self.client)
        return user
