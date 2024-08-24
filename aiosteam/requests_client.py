import json

from aiohttp import ClientSession

from .constants import API_BASE_URL
from .utils import build_url_with_params, merge_dict, retry, validator, create_session


class RequestsClient:
    """Steams API HTTP client"""

    def __init__(self, key: str, headers: dict = None):
        if not headers:
            headers = {}
        """Constructor for TypeForm API client"""
        self.__headers = merge_dict({"Content-Type": "application/json", "Accept": "application/json"}, headers)
        self.key = key

    @retry(times=3, exceptions=(ValueError, TypeError))
    @create_session
    async def request(self, method: str, url: str, data=None, params=None, headers=None, session: ClientSession = None,
                      timeout: int = 3, **kwargs) -> str or dict:

        if headers is None:
            headers = {}
        if params is None:
            params = {}
        if data is None:
            data = {}

        request_url = build_url_with_params((API_BASE_URL + url), self.key, params)

        request_headers = merge_dict(self.__headers, headers)
        request_data = ""
        if type(data) is dict:
            request_data = json.dumps(data) if data.keys() else ""

        if type(data) is list:
            request_data = json.dumps(data) if data else ""
        resp = await session.request(method, request_url, data=request_data, headers=request_headers, timeout=timeout,
                                     **kwargs)
        return await validator(resp)
