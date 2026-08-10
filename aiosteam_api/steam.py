
from aiosteam_api.clients.requests_client import RequestsClient
from aiosteam_api.constants import DEFAULT_MAX_CONCURRENCY, DEFAULT_TIMEOUT
from aiosteam_api.steam_models import User


class Steam:
    """Steam API client

    Every call opens its own HTTP session unless the client is used as an async context manager,
    which keeps a single session (and its connection pool) alive for all of them:

        async with Steam(key) as steam:
            user = await steam.search_user("jeygavrus")
            await user.get_all_info()
    """

    def __init__(self, key: str, headers=None, timeout: float = DEFAULT_TIMEOUT,
                 max_concurrency: int = DEFAULT_MAX_CONCURRENCY):
        """Constructor for Steam API client

        Args:
            key (str): Steam Web API key
            headers (dict, optional): extra headers to send with every request
            timeout (float, optional): total timeout of a single request, in seconds
            max_concurrency (int, optional): how many requests may be in flight at the same time
        """
        if headers is None:
            headers = {}
        self.client = RequestsClient(key, headers=headers, timeout=timeout, max_concurrency=max_concurrency)
        self.__users = User

    async def __aenter__(self) -> "Steam":
        await self.client.open()
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        await self.client.close()

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

    async def get_published_file_details(
            self,
            published_file_ids: list[int],
            include_tags: bool = True,
            include_additional_previews: bool = True,
            include_children: bool = True,
            include_kv_tags: bool = True,
            include_votes: bool = True,
            short_description: bool = True,
            include_for_sale_data: bool = True,
            include_metadata: bool = True,
            language: int | None = None,
            return_playtime_stats: int = 30,
            app_id: int | None = None,
            strip_description_bbcode: bool = True,
            desired_revision: int | None = None,
            include_reactions: bool = False,
            admin_query: bool = True,
    ) -> dict:
        """Queries Workshop files with the Steamworks Web API

        This one hangs off the client rather than off a User or a Game, because a published file
        belongs to neither.

        Args:
            published_file_ids (list[int]): Set of published file IDs to retrieve details for.
            include_tags (bool): If true, return tag information in the returned details.
            include_additional_previews (bool): If true, return preview information in the returned details.
            include_children (bool): If true, return children in the returned details.
            include_kv_tags (bool): If true, return key value tags in the returned details.
            include_votes (bool): If true, return vote data in the returned details.
            short_description (bool): If true, return a short description instead of the full description.
            include_for_sale_data (bool): If true, return pricing data, if applicable.
            include_metadata (bool): If true, populate the metadata field.
            language (int, optional): Specifies the localized text to return. Defaults to English.
            return_playtime_stats (int): Return playtime stats for the specified number of days before today.
            app_id (int, optional): App ID associated with the published files.
            strip_description_bbcode (bool): Strips BBCode from descriptions.
            desired_revision (int, optional): Return the data for the specified revision.
            include_reactions (bool): If true, reactions to items will be returned.
            admin_query (bool): If true, return hidden items.
        """
        params = {
            "includetags": include_tags,
            "includeadditionalpreviews": include_additional_previews,
            "includechildren": include_children,
            "includekvtags": include_kv_tags,
            "includevotes": include_votes,
            "short_description": short_description,
            "includeforsaledata": include_for_sale_data,
            "includemetadata": include_metadata,
            "language": language,
            "return_playtime_stats": return_playtime_stats,
            "appid": app_id,
            "strip_description_bbcode": strip_description_bbcode,
            "desired_revision": desired_revision,
            "includereactions": include_reactions,
            "admin_query": admin_query,
        }
        for index, file_id in enumerate(published_file_ids):
            params[f"publishedfileids[{index}]"] = file_id

        return await self.client.request("get", "/IPublishedFileService/GetDetails/v1/", params=params)
