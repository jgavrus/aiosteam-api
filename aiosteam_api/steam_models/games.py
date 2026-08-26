import asyncio
import datetime
import re

from pydantic import BaseModel, ConfigDict, model_validator

from aiosteam_api.clients.requests_client import RequestsClient

# Steam localizes the release date string, and it is not always a single day ("Q1 2026", "Coming soon"),
# so ReleaseDate.as_date tries these and gives up rather than guessing.
_RELEASE_DATE_FORMATS = ("%d %b, %Y", "%b %d, %Y", "%d %B, %Y", "%B %d, %Y", "%b %Y", "%B %Y", "%Y")


class PriceOverview(BaseModel):
    """A store price. ``initial``/``final`` are in hundredths of ``currency`` (179900 == 1799.00 UAH),
    while the ``*_formatted`` strings come ready to print — ``initial_formatted`` is empty unless the
    app is discounted."""

    currency: str | None = None
    initial: int | None = None
    final: int | None = None
    discount_percent: int | None = None
    initial_formatted: str | None = None
    final_formatted: str | None = None

    @property
    def final_price(self) -> float | None:
        return None if self.final is None else self.final / 100

    @property
    def initial_price(self) -> float | None:
        return None if self.initial is None else self.initial / 100


class Metacritic(BaseModel):
    score: int | None = None
    url: str | None = None


class ReleaseDate(BaseModel):
    coming_soon: bool | None = None
    date: str | None = None

    @property
    def as_date(self) -> datetime.date | None:
        """The date string as a real date, or None when Steam gave something that is not one day"""
        for date_format in _RELEASE_DATE_FORMATS:
            try:
                return datetime.datetime.strptime(self.date, date_format).date()
            except (TypeError, ValueError):
                continue
        return None


class Platforms(BaseModel):
    windows: bool | None = None
    mac: bool | None = None
    linux: bool | None = None


class StoreTag(BaseModel):
    """One genre or category. Steam sends genre ids as strings and category ids as ints"""

    id: int | None = None
    description: str | None = None


class AppAchievements(BaseModel):
    """How many achievements the app has — not the player's progress, that is Game.player_achievements"""

    total: int | None = None
    highlighted: list[dict] | None = None


class Recommendations(BaseModel):
    total: int | None = None


class SupportInfo(BaseModel):
    url: str | None = None
    email: str | None = None


class ContentDescriptors(BaseModel):
    ids: list[int] | None = None
    notes: str | None = None


class PlayerAchievement(BaseModel):
    """One achievement of one player, from GetPlayerAchievements.

    ``name``/``description`` are only there when the app publishes them; hidden achievements come back
    without a description.
    """

    api_name: str | None = None
    achieved: bool | None = None
    unlock_time: int | None = None
    name: str | None = None
    description: str | None = None

    @model_validator(mode='before')
    def normalize_steam_keys(cls, inp: dict):
        if not isinstance(inp, dict):
            return inp

        for steam_key, field in (('apiname', 'api_name'), ('unlocktime', 'unlock_time')):
            if steam_key in inp:
                inp[field] = inp.pop(steam_key)

        return inp


class Game(BaseModel):
    # validate_assignment turns the dicts of an appdetails payload into the models above as they are
    # assigned, which is what lets apply_app_details() copy the payload over field by field
    model_config = ConfigDict(arbitrary_types_allowed=True, validate_assignment=True)
    client: RequestsClient
    app_id: int
    name: str

    # GetOwnedGames / GetRecentlyPlayedGames — all playtimes are in minutes
    playtime_forever: int | None = None
    img_icon_url: str | None = None
    playtime_two_weeks: int | None = None
    playtime_windows_forever: int | None = None
    playtime_mac_forever: int | None = None
    playtime_linux_forever: int | None = None
    playtime_deck_forever: int | None = None
    playtime_disconnected: int | None = None
    rtime_last_played: int | None = None
    has_community_visible_stats: bool | None = None
    content_descriptorids: list[int] | None = None

    # player stats and achievements
    user_stats: dict | None = {}
    user_achievements: dict | None = {}
    player_achievements: list[PlayerAchievement] | None = None
    player_achievement_statistics: dict | None = {}
    from_user_id: int | None = None

    # store appdetails
    type: str | None = None
    required_age: int | None = None
    is_free: bool | None = None
    controller_support: str | None = None
    dlc: list['Game'] | None = None
    fullgame: dict | None = None
    detailed_description: str | None = None
    about_the_game: str | None = None
    short_description: str | None = None
    reviews: str | None = None
    supported_languages: dict[str, str] | None = None
    header_image: str | None = None
    capsule_image: str | None = None
    capsule_imagev5: str | None = None
    background: str | None = None
    background_raw: str | None = None
    screenshots: list[dict] | None = None
    movies: list[dict] | None = None
    website: str | None = None
    developers: list[str] | None = None
    publishers: list[str] | None = None
    demos: list[dict] | None = None
    price_overview: PriceOverview | None = None
    packages: list[int] | None = None
    package_groups: list[dict] | None = None
    platforms: Platforms | None = None
    metacritic: Metacritic | None = None
    categories: list[StoreTag] | None = None
    genres: list[StoreTag] | None = None
    recommendations: Recommendations | None = None
    achievements: AppAchievements | None = None
    release_date: ReleaseDate | None = None
    support_info: SupportInfo | None = None
    content_descriptors: ContentDescriptors | None = None
    ratings: dict | None = None
    legal_notice: str | None = None
    drm_notice: str | None = None
    ext_user_account_notice: str | None = None
    pc_requirements: dict | list | None = None
    mac_requirements: dict | list | None = None
    linux_requirements: dict | list | None = None

    # appdetails keys that must not be copied onto the model as they come:
    # the ids identify the app (they are set when the Game is built) and `dlc` is a list of app ids,
    # which is not a list of Games — get_info_from_shop() fetches those separately.
    _APP_DETAILS_SKIP = frozenset({'steam_appid', 'appid', 'dlc'})

    @model_validator(mode='before')
    def normalize_steam_keys(cls, inp: dict):
        """Maps the store's own key names onto the model's. Only renames keys that are actually there,
        so a Game can also be built from already normalized data (e.g. its own model_dump())."""
        if not isinstance(inp, dict):
            return inp

        if 'playtime_2weeks' in inp:
            inp["playtime_two_weeks"] = inp.pop('playtime_2weeks')

        app_id = inp.pop('appid', None) or inp.pop('steam_appid', None)
        if app_id is not None:
            inp["app_id"] = app_id

        return inp

    @classmethod
    def from_app_details(cls, details: dict, client, from_user_id: int | None = None) -> 'Game':
        """Builds a Game straight from a store appdetails payload"""
        game = cls(client=client, app_id=details.get('steam_appid') or details.get('appid'),
                   name=details.get('name') or '', from_user_id=from_user_id)
        game.apply_app_details(details)
        return game

    def apply_app_details(self, details: dict) -> 'Game':
        """Copies a store appdetails payload onto this game.

        Every key Steam sends is copied onto the field of the same name, so a payload that grows a new
        key only needs that field declared above — nothing is filtered by hand. The two keys that are
        not usable as they come (`required_age`, `supported_languages`) are parsed on the way in.
        """
        if not details:
            return self

        fields = type(self).model_fields
        for key, value in details.items():
            if key in self._APP_DETAILS_SKIP or key not in fields:
                continue
            if key == 'required_age':
                value = self.parse_required_age(value)
            elif key == 'supported_languages':
                value = self.parse_supported_languages(value)
            setattr(self, key, value)

        return self

    @staticmethod
    def parse_supported_languages(text: str | None) -> dict[str, str]:
        """Parses the store's supported_languages string into {language: 'full' | 'text'}

        Steam returns something like
        "English<strong>*</strong>, French, German<br><strong>*</strong>languages with full audio support",
        where the asterisk marks full audio support and everything after the <br> is a footnote.
        """
        if not text:
            return {}
        languages = re.split(r'<br\s*/?>', text)[0]
        result = {}
        for row in languages.split(', '):
            name = row.split('<')[0].strip()
            if not name:
                continue
            result[name] = 'full' if '<' in row else 'text'
        return result

    @staticmethod
    def parse_required_age(value) -> int | None:
        """The store returns required_age as an int, as "0", or as "18+" depending on the app"""
        if value is None or isinstance(value, bool):
            return None
        if isinstance(value, int):
            return value
        age = re.search(r'\d+', str(value))
        return int(age.group()) if age else None

    @property
    def last_played(self) -> datetime.datetime | None:
        """When the player last launched the game, from GetOwnedGames' rtime_last_played"""
        if not self.rtime_last_played:
            return None
        return datetime.datetime.fromtimestamp(self.rtime_last_played)

    @property
    def unlocked_achievements(self) -> int | None:
        """How many achievements this player has unlocked, once get_user_achievements() has run"""
        if self.player_achievements is None:
            return None
        return sum(1 for achievement in self.player_achievements if achievement.achieved)

    async def get_user_stats(self) -> dict:
        """Obtains a user's stats for a specific app, includes only completed achievements
        along with app specific information"""
        response = await self.client.request("get", "/ISteamUserStats/GetUserStatsForGame/v2/",
                                             params={"steamid": self.from_user_id, "appid": self.app_id})
        self.player_achievement_statistics.update(response)
        return self.player_achievement_statistics

    async def get_user_achievements(self, language: str = "en") -> list[PlayerAchievement]:
        """Obtains information of the user's achievments in the app

        Returns the parsed achievements and leaves the whole raw response (which also carries the app
        name and Steam's error message for a private profile) in `self.user_achievements`.

        Args:
            language (str): abbreviated language the achievement names are returned in
        """
        response = await self.client.request("get", "/ISteamUserStats/GetPlayerAchievements/v1/",
                                             params={"steamid": self.from_user_id, "appid": self.app_id,
                                                     "l": language})
        if isinstance(response, dict):
            self.user_achievements.update(response)

        achievements = (self.user_achievements.get("playerstats") or {}).get("achievements") or []
        self.player_achievements = [PlayerAchievement.model_validate(achievement)
                                    for achievement in achievements]
        return self.player_achievements

    async def get_info_from_shop(self, country: str = "US", filters: str | None = None) -> 'Game':
        """Fills the game in from the store.

        Args:
            country (str): ISO country code of the store to read — the price comes back in that
                store's currency, so this is the difference between $29.99 and 1 799₴.
            filters (str, optional): None, the default, asks for the whole appdetails payload. The
                store's own "basic" filter leaves out the price, the genres, the release date and the
                ratings, all of which this model parses; pass a comma-separated list to fetch less.
        """
        game = await self.client.get_app_details(app_id=self.app_id, country=country, filters=filters)
        self.apply_app_details(game)

        if dlc_ids := game.get('dlc') or []:
            dlc_details = await asyncio.gather(*(self.client.get_app_details(app_id=dlc_id, country=country,
                                                                            filters=filters)
                                                 for dlc_id in dlc_ids))
            self.dlc = [Game.from_app_details(details, self.client, self.from_user_id)
                        for details in dlc_details if details]
        return self

    async def get_all_info(self, language: str = "en", country: str = "US"):
        await asyncio.gather(
            self.get_info_from_shop(country=country),
            self.get_user_achievements(language),
            self.get_user_stats(),
        )
        return self
