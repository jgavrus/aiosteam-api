import asyncio
import functools
import logging
from urllib.parse import urlencode

import aiohttp
from aiohttp.client import ClientResponse

from aiosteam_api.exceptions.api_errors import InvalidKey, RateLimited, SteamAPIError

logger = logging.getLogger(__name__)


def build_url_with_params(url: str, key: str, params=None) -> str:
    if params is None:
        params = {}
    encoded = urlencode(clean_dict(params))
    return url + "?key=" + key if len(encoded) == 0 else (url + "?key=" + key + "&" + encoded)


def build_url_with_params_for_search(url: str, search: str, params=None) -> str:
    if params is None:
        params = {}
    encoded = urlencode(clean_dict(params))
    return url + "?term=" + search if (len(encoded) == 0) else (url + "?term=" + search + "&" + encoded)


def clean_dict(x=None) -> dict:
    if x is None:
        x = {}
    result = {}
    for key in x:
        # only None is dropped: 0 and False are meaningful to Steam (include_own=0, admin_query=false)
        if x[key] is not None:
            # Check If List
            if isinstance(x[key], list):
                result[key] = ",".join(str(item) for item in x[key])
            # Check If Boolean
            elif isinstance(x[key], bool):
                if x[key] is True:
                    result[key] = "true"
                else:
                    result[key] = "false"
            # Everything Else (Strings/Numbers)
            else:
                result[key] = x[key]
    return result


def merge_dict(x: dict, y: dict) -> dict:
    z = clean_dict(x)
    z.update(clean_dict(y))
    return z


async def validator(result: ClientResponse) -> str | dict:
    try:
        body = await result.json(content_type=None)
    except (ValueError, aiohttp.ClientError):
        body = await result.text()

    if result.status == 429:
        raise RateLimited("429, too many requests to the Steam API", retry_after=retry_after(result))
    elif result.status in (401, 403):
        raise InvalidKey(f"{result.status}, {result.reason}: the API key is missing, invalid or has no access "
                         f"to this resource", status=result.status)
    elif isinstance(body, dict) and body.get("code"):
        raise SteamAPIError(body.get("description"), status=result.status)
    elif result.status >= 400:
        raise SteamAPIError(f"{result.status}, {result.reason}", status=result.status)
    elif body is None or (isinstance(body, str) and not body):
        # only a genuinely empty body becomes "OK": an empty json object is still an answer,
        # and callers do .get() on it
        return "OK"
    else:
        return body


def retry_after(result: ClientResponse) -> float | None:
    """Reads the Retry-After header, which Steam only sometimes sends along with a 429"""
    try:
        return float(result.headers.get("Retry-After"))
    except (TypeError, ValueError):
        return None


def retry(times, exceptions, backoff: float = 0.5):
    """
    Retry Decorator
    Retries the wrapped coroutine `times` times if the exceptions listed in ``exceptions`` are thrown,
    waiting `backoff` seconds and doubling that wait after every attempt. A 429 is always retried,
    honouring Retry-After when Steam sends it. The last exception is re-raised once the attempts run out.
    :param times: The number of times to repeat the wrapped coroutine
    :type times: Int
    :param exceptions: Lists of exceptions that trigger a retry attempt
    :type exceptions: Tuple of Exceptions
    :param backoff: Seconds to wait before the second attempt, doubled for every further attempt
    :type backoff: Float
    """

    def decorator(func):
        @functools.wraps(func)
        async def new_fn(*args, **kwargs):
            last_exception = None
            for attempt in range(times):
                try:
                    return await func(*args, **kwargs)
                except RateLimited as exc:
                    last_exception = exc
                    delay = exc.retry_after if exc.retry_after is not None else backoff * 2 ** attempt
                except exceptions as exc:
                    last_exception = exc
                    delay = backoff * 2 ** attempt
                logger.warning("Exception thrown when attempting to run %s, attempt %d of %d: %r",
                               func.__name__, attempt + 1, times, last_exception)
                if attempt + 1 < times:
                    await asyncio.sleep(delay)
            raise last_exception

        return new_fn

    return decorator
