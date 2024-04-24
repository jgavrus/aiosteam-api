import json
from urllib.parse import urlencode

import aiohttp
from aiohttp.client import ClientResponse


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
        if x[key]:
            # Check If List
            if isinstance(x[key], list):
                result[key] = ",".join(x[key])
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


async def validator(result: ClientResponse) -> str or dict:
    try:
        body = await result.json()
    except aiohttp.ContentTypeError:
        body = await result.text()
    except Exception as e:
        print(e)
        body = {}

    if isinstance(body, dict) and body.get("code"):
        raise Exception(body.get("description"))
    elif result.status >= 400:
        raise Exception(f"{result.status}, {result.reason}")
    elif not body:
        return "OK"
    else:
        return body


def retry(times, exceptions):
    """
    Retry Decorator
    Retries the wrapped function/method `times` times if the exceptions listed
    in ``exceptions`` are thrown
    :param times: The number of times to repeat the wrapped function/method
    :type times: Int
    :param exceptions: Lists of exceptions that trigger a retry attempt
    :type exceptions: Tuple of Exceptions
    """

    def decorator(func):
        async def new_fn(*args, **kwargs):
            for attempt in range(times):
                try:
                    return await func(*args, **kwargs)
                except exceptions:
                    print(f'Exception thrown when attempting to run {func.__name__}, attempt {attempt + 1} of {times}')
            return func(*args, **kwargs)

        return new_fn

    return decorator


def create_session(fn):
    async def wrapper(*args, **kwargs):
        async with aiohttp.ClientSession() as session:
            return await fn(*args, session=session, **kwargs)

    return wrapper
