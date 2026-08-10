from aioresponses import aioresponses

from aiosteam_api import Steam
from aiosteam_api.steam_types import PublishedFileInfoMatchingFileType, PublishedFileQueryType
from conftest import KEY, PUBLISHED_FILES, SUMMARIES, requested_urls, summaries

STEAM_ID = 76561198144619553


async def test_async_context_manager_opens_and_closes_the_shared_session():
    async with Steam(KEY) as steam:
        assert steam.client._session is not None and not steam.client._session.closed
        session = steam.client._session

        with aioresponses() as mocked:
            mocked.get(SUMMARIES, payload=summaries(STEAM_ID))
            user = await steam.search_user(steam_id=STEAM_ID)

    assert user.steam_id == STEAM_ID
    assert session.closed, "leaving the context has to close the session"
    assert steam.client._session is None


async def test_steam_still_works_without_the_context_manager(steam):
    with aioresponses() as mocked:
        mocked.get(SUMMARIES, payload=summaries(STEAM_ID))
        user = await steam.search_user(steam_id=STEAM_ID)

    assert user.steam_id == STEAM_ID
    assert steam.client._session is None


async def test_get_published_file_details_indexes_the_file_ids(steam):
    with aioresponses() as mocked:
        mocked.get(PUBLISHED_FILES, payload={"response": {"publishedfiledetails": []}})
        await steam.get_published_file_details([111, 222])

    url = requested_urls(mocked)[0]
    assert "publishedfileids%5B0%5D=111" in url
    assert "publishedfileids%5B1%5D=222" in url
    assert f"key={KEY}" in url, "the client's key is used, it is not a separate argument"


async def test_get_published_file_details_keeps_false_flags(steam):
    """These flags mean something to Steam, so they have to be sent as false rather than dropped"""
    with aioresponses() as mocked:
        mocked.get(PUBLISHED_FILES, payload={"response": {}})
        await steam.get_published_file_details([111], include_reactions=False, admin_query=True,
                                               return_playtime_stats=0)

    url = requested_urls(mocked)[0]
    assert "includereactions=false" in url
    assert "admin_query=true" in url
    assert "return_playtime_stats=0" in url
    assert "language" not in url, "unset optional parameters are left out entirely"


def test_published_file_enums_are_available():
    assert PublishedFileQueryType.RANKED_BY_TEXT_SEARCH == 12
    assert PublishedFileInfoMatchingFileType.COLLECTIONS == 1
