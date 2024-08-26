from typing import Optional

import aiohttp
from aiohttp import ClientSession
from bs4 import BeautifulSoup

from .utils import build_url_with_params, merge_dict, retry, validator, build_url_with_params_for_search


def create_session(fn):
    async def wrapper(*args, **kwargs):
        async with aiohttp.ClientSession() as session:
            return await fn(*args, session=session, **kwargs)

    return wrapper


class RequestsClient:
    """Steams API HTTP client"""

    def __init__(self, key: str, headers: dict = None):
        if not headers:
            headers = {}
        """Constructor for TypeForm API client"""
        self.__headers = merge_dict({"Content-Type": "application/json", "Accept": "application/json"}, headers)
        self.key = key
        self.api_base_url = "https://api.steampowered.com"
        self.search_url = "https://store.steampowered.com/search/suggest"
        self.app_details_url = "https://store.steampowered.com/api/appdetails"

    @create_session
    async def get_app_details(self, app_id: int, country="US", filters: Optional[str] = "basic",
                              session: ClientSession = None) -> dict:
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
        response = await session.request('get', self.app_details_url,
                                         params={"appids": app_id, "cc": country, "filters": filters})
        dict_response = await response.json()
        return dict_response.get(str(app_id), {}).get('data', {})

    @retry(times=3, exceptions=(ValueError, TypeError))
    @create_session
    async def request(self, method: str, url: str, params=None, headers=None, session: ClientSession = None,
                      timeout: int = 3, **kwargs) -> str or dict:

        if headers is None:
            headers = {}
        if params is None:
            params = {}

        request_url = build_url_with_params((self.api_base_url + url), self.key, params)

        request_headers = merge_dict(self.__headers, headers)

        resp = await session.request(method, request_url, headers=request_headers, timeout=timeout, **kwargs)
        return await validator(resp)

    @retry(times=3, exceptions=(ValueError, TypeError))
    @create_session
    async def search_games(self, term, country="US", session: ClientSession = None):
        """Searches for games using the information given
        Args:
            term (Any): Search term
            country (str): ISO Country Code
            session: aiohttp.ClientSession, optional added unfathomably from decorator

        """
        url = self.create_search_url(term, country)
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
    # (Maybe change it to all caps since search_url and app_details_url are constants?)
    def create_search_url(self, search, country="US"):
        params = {"f": "games", "cc": country, "realm": 1, "l": "english"}
        result = build_url_with_params_for_search(self.search_url, search, params=params)
        return result
