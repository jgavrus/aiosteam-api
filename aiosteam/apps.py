import json

import typing
from aiohttp import ClientSession
from .requests_client import RequestsClient
from .utils import build_url_with_params_for_search, validator, create_session
from bs4 import BeautifulSoup
from .constants import API_APP_DETAILS_URL, API_APP_SEARCH_URL


class Apps:
    """Steam Apps API client"""

    def __init__(self, client: RequestsClient):
        """Constructor for Steam Apps class"""
        self.__client = client
        self.__search_url = API_APP_SEARCH_URL
        self.__app_details_url = API_APP_DETAILS_URL

    @create_session
    async def get_app_details(self, app_id: int, country="US",
                              filters: typing.Optional[str] = "basic", session: ClientSession = None) -> dict:
        """Obtains an apps details
        
        Args:
            app_id (int): App ID. For example 546560 (Half-Life-Alyx)
            country (str): ISO Country Code
            session: aiohttp.ClientSession, optional added unfathomably from decorator
            filters (str): list of keys to return, e.g. "name,platforms,price_overview". If you use multiple appids, you must set this parameter to "price_overview".
                The filter basic returns the following keys:
                    type
                    name
                    steam_appid
                    required_age
                    dlc
                    detailed_description
                    about_the_game
                    supported_languages
                    detailed_description
                    supported_languages
                    header_image
                    website
                    pc_requirements
                    mac_requirements
                    linux_requirements
                Any key names except those listed under basic are acceptable as filter values.
                Optional filters:
                    controller_support,
                    fullgame,
                    legal_notice,
                    developers,
                    demos,
                    price_overview,
                    metacritic,
                    categories,
                    genres,
                    screenshots,
                    movies,
                    recommendations,
                    achievements,
        """
        response = await session.request('get', self.__app_details_url,
                                         params={"appids": app_id, "cc": country, "filters": filters})
        json_loaded_response = json.loads(await response.text())
        return json_loaded_response

    async def get_user_stats(self, steam_id: int or str, app_id: int or str) -> dict:
        """Obtains a user's stats for a specific app, includes only completed achievements
        along with app specific information
        
        Args:
            steam_id (int): Steam 64 ID
            app_id (int): App ID
        """
        response = await self.__client.request("get", "/ISteamUserStats/GetUserStatsForGame/v2/",
                                               params={"steamid": steam_id, "appid": app_id})
        return response

    async def get_user_achievements(self, steam_id: int or str, app_id: int or str) -> dict:
        """Obtains information of the user's achievments in the app
        
        Args:
            steam_id (int): Steam 64 ID
            app_id (int): App ID
        """
        response = await self.__client.request("get", "/ISteamUserStats/GetPlayerAchievements/v1/",
                                               params={"steamid": steam_id, "appid": app_id})
        return response

    # Is term meant to be any or a string, I'm not familiar enough with async_steam search so I'll leave it as is
    @create_session
    async def search_games(self, term, country="US", session: ClientSession = None):
        """Searches for games using the information given
        Args:
            term (Any): Search term
            country (str): ISO Country Code
            session: aiohttp.ClientSession, optional added unfathomably from decorator

        """
        url = self.search_url(term, country)
        result = await session.request("get", url)
        html = await validator(result)
        soup = BeautifulSoup(html, features="html.parser")
        links = soup.find_all("a")
        apps = []
        for link in links:
            if link.has_attr("data-ds-appid"):
                app = {}
                string_id = link["data-ds-appid"]
                href = link["href"].replace("\\", "").replace('"', "")
                app["id"] = [int(i) for i in string_id.replace("\\", "").replace('"', "").split(',')]
                app["link"] = href
                divs = link.select("div")
                for div in divs:
                    if div["class"][0] == "match_name":
                        app["name"] = div.text
                    if div["class"][0] == "match_price":
                        app["price"] = div.text
                    if div["class"][0] == "match_img":
                        app["img"] = div.img["src"].replace("\\", "").replace('"', "")
                apps.append(app)
        return {"apps": apps}

    # This should be a private method imo, I don't know how you would like to name them so I'll leave it as is
    # (Maybe change it to all caps since __search_url and __app_details_url are constants?)
    def search_url(self, search, country="US"):
        params = {"f": "games", "cc": country, "realm": 1, "l": "english"}
        result = build_url_with_params_for_search(self.__search_url, search, params=params)
        return result
