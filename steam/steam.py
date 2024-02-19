from .users import Users
from .client import Client
from .apps import Apps


class Steam:
    """Steam API client"""

    def __init__(self, key: str, headers=None):
        """Constructor for Steam API client"""
        if headers is None:
            headers = {}
        client = Client(key, headers=headers)
        self.__users = Users(client)
        self.__apps = Apps(client)

    @property
    def users(self) -> Users:
        return self.__users

    @property
    def apps(self) -> Apps:
        return self.__apps
