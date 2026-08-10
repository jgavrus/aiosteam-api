class SteamAPIError(Exception):
    """Base class for every error this library raises"""

    def __init__(self, message: str, status: int = None):
        super().__init__(message)
        self.status = status


class NotFound(SteamAPIError):
    """The requested user or app does not exist, is private or is banned"""


class InvalidKey(SteamAPIError):
    """Steam rejected the API key, or the key has no access to this resource"""


class RateLimited(SteamAPIError):
    """Steam answered with 429 Too Many Requests"""

    def __init__(self, message: str, status: int = 429, retry_after: float = None):
        super().__init__(message, status)
        self.retry_after = retry_after
