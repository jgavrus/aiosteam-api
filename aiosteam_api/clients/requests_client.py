import asyncio
import functools
from contextlib import asynccontextmanager

import aiohttp
from aiohttp import ClientSession
from bs4 import BeautifulSoup

from aiosteam_api.constants import (API_BASE_URL, APP_DETAILS_URL, APP_SEARCH_URL, DEFAULT_MAX_CONCURRENCY,
                                    DEFAULT_RETRIES, DEFAULT_TIMEOUT)

from .utils import build_url_with_params, merge_dict, retry, validator, build_url_with_params_for_search

RETRYABLE = (aiohttp.ClientError, asyncio.TimeoutError, ValueError, TypeError)


def create_session(fn):
    """Injects an aiohttp session into the wrapped method.

    Reuses the client's shared session when the client is open (``async with Steam(key) as steam``),
    otherwise opens a throwaway session that lives for this single call.
    """

    @functools.wraps(fn)
    async def wrapper(self, *args, **kwargs):
        if kwargs.get("session") is not None:
            return await fn(self, *args, **kwargs)
        async with self.session_scope() as session:
            return await fn(self, *args, session=session, **kwargs)

    return wrapper


class RequestsClient:
    """Steams API HTTP client"""

    def __init__(self, key: str, headers: dict = None, timeout: float = DEFAULT_TIMEOUT,
                 max_concurrency: int = DEFAULT_MAX_CONCURRENCY):
        if not headers:
            headers = {}
        """Constructor for TypeForm API client"""
        self.__headers = merge_dict({"Content-Type": "application/json", "Accept": "application/json"}, headers)
        self.key = key
        self.api_base_url = API_BASE_URL
        self.search_url = APP_SEARCH_URL
        self.app_details_url = APP_DETAILS_URL
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self.max_concurrency = max_concurrency
        self._semaphore = asyncio.Semaphore(max_concurrency)
        self._session: ClientSession | None = None

    async def open(self) -> "RequestsClient":
        """Opens one session to be shared by every following request until close() is called"""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(timeout=self.timeout)
        return self

    async def close(self) -> None:
        """Closes the shared session, if there is one"""
        if self._session is not None and not self._session.closed:
            await self._session.close()
        self._session = None

    @asynccontextmanager
    async def session_scope(self):
        """Yields the shared session when the client is open, a single-use session otherwise"""
        if self._session is not None and not self._session.closed:
            yield self._session
            return

        session = aiohttp.ClientSession(timeout=self.timeout)
        try:
            yield session
        finally:
            await session.close()

    async def _send(self, session: ClientSession, method: str, url: str, **kwargs) -> str | dict:
        """Performs a single HTTP call, never more than `max_concurrency` of them at the same time"""
        async with self._semaphore:
            async with session.request(method, url, **kwargs) as response:
                return await validator(response)

    def _timeout(self, timeout: float = None) -> aiohttp.ClientTimeout:
        return self.timeout if timeout is None else aiohttp.ClientTimeout(total=timeout)

    @retry(times=DEFAULT_RETRIES, exceptions=RETRYABLE)
    @create_session
    async def get_app_details(self, app_id: int, country="US", filters: str | None = "basic",
                              session: ClientSession = None) -> dict:
        """Obtains an apps details

        Args:
            app_id (int): App ID. For example 546560 (Half-Life-Alyx)
            country (str): ISO Country Code
            session: aiohttp.ClientSession, optional added unfathomably from decorator
            filters (str): list of keys to return, e.g. "name,platforms,price_overview". If you use
            multiple appids, you must set this parameter to "price_overview".
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
        response = await self._send(session, 'get', self.app_details_url, timeout=self._timeout(),
                                    params={"appids": app_id, "cc": country, "filters": filters})
        if not isinstance(response, dict):
            return {}
        return response.get(str(app_id), {}).get('data', {})

    @retry(times=DEFAULT_RETRIES, exceptions=RETRYABLE)
    @create_session
    async def request(self, method: str, url: str, params=None, headers=None, session: ClientSession = None,
                      timeout: float = None, **kwargs) -> str | dict:

        if headers is None:
            headers = {}
        if params is None:
            params = {}

        request_url = build_url_with_params((self.api_base_url + url), self.key, params)

        request_headers = merge_dict(self.__headers, headers)

        return await self._send(session, method, request_url, headers=request_headers,
                                timeout=self._timeout(timeout), **kwargs)

    @retry(times=DEFAULT_RETRIES, exceptions=RETRYABLE)
    @create_session
    async def search_games(self, term, country="US", fetch_discounts: bool = False,
                           session: ClientSession = None) -> dict:
        """Searches for games using the information given
        Args:
            term (Any): Search term
            country (str): ISO Country Code
            fetch_discounts (bool): Opens the store page of every result to read its discount. That is one
                extra request per result, so they are all issued concurrently.
            session: aiohttp.ClientSession, optional added unfathomably from decorator

        """
        url = self.create_search_url(term, country)
        html = await self._send(session, "get", url, timeout=self._timeout())
        apps = self._parse_search_results(html)

        if fetch_discounts and apps:
            discounts = await asyncio.gather(*(self._get_discount(app["link"], session) for app in apps))
            for app, discount in zip(apps, discounts, strict=True):
                app.update(discount)

        return {"apps": apps}

    async def _get_discount(self, link: str, session: ClientSession) -> dict:
        """Reads the discount countdown off a store page, if the app is on sale"""
        discount = {"has_discount": False, "discount": None}
        html = await self._send(session, "get", link, timeout=self._timeout())
        if not isinstance(html, str):
            return discount

        soup = BeautifulSoup(html, features="html.parser")
        countdown = soup.find(class_="game_purchase_discount_countdown")
        if countdown is not None:
            discount["has_discount"] = True
            discount["discount"] = countdown.text.strip()
        return discount

    @staticmethod
    def _parse_search_results(html) -> list[dict]:
        if not isinstance(html, str):
            return []

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
                divs = link.find_all("div")
                for div in divs:
                    class_names = div.get("class") or []
                    if not class_names:
                        continue
                    if class_names[0] == "match_name":
                        app["name"] = div.text
                    if class_names[0] == "match_price":
                        app["price"] = div.text
                    if class_names[0] == "match_img":
                        img = div.find("img")
                        if img is not None and img.has_attr("src"):
                            app["img"] = img["src"].replace("\\", "").replace('"', "")
                apps.append(app)
        return apps

    # This should be a private method imo, I don't know how you would like to name them so I'll leave it as is
    # (Maybe change it to all caps since search_url and app_details_url are constants?)
    def create_search_url(self, search, country="US"):
        params = {"f": "games", "cc": country, "realm": 1, "l": "english"}
        result = build_url_with_params_for_search(self.search_url, search, params=params)
        return result
