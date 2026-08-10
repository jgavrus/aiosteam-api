import asyncio
import re

from pydantic import BaseModel, model_validator, ConfigDict

from aiosteam_api.clients.requests_client import RequestsClient


class Game(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    client: RequestsClient
    app_id: int
    name: str
    playtime_forever: int | None = None
    img_icon_url: str | None = None
    playtime_two_weeks: int | None = None
    user_stats: dict | None = {}
    user_achievements: dict | None = {}
    from_user_id: int | None = None
    required_age: int | None = None
    is_free: bool | None = None
    dlc: list['Game'] | None = None
    detailed_description: str | None = None
    about_the_game: str | None = None
    short_description: str | None = None
    supported_languages: dict[str, str] | None = None
    header_image: str | None = None
    capsule_image: str | None = None
    capsule_imagev5: str | None = None
    website: str | None = None
    pc_requirements: dict | list | None = None
    mac_requirements: dict | list | None = None
    linux_requirements: dict | list | None = None
    player_achievement_statistics: dict | None = {}

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
        """Copies a store appdetails payload onto this game, parsing the fields that need it.

        `dlc` is skipped on purpose: appdetails returns it as a list of app ids, and turning those into
        Game objects costs one request each (see get_info_from_shop).
        """
        self.required_age = self.parse_required_age(details.get('required_age'))
        self.is_free = details.get('is_free')
        self.detailed_description = details.get('detailed_description')
        self.about_the_game = details.get('about_the_game')
        self.short_description = details.get('short_description')
        self.supported_languages = self.parse_supported_languages(details.get('supported_languages'))
        self.pc_requirements = details.get('pc_requirements')
        self.mac_requirements = details.get('mac_requirements')
        self.linux_requirements = details.get('linux_requirements')
        self.header_image = details.get('header_image')
        self.capsule_image = details.get('capsule_image')
        self.capsule_imagev5 = details.get('capsule_imagev5')
        self.website = details.get('website')
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

    async def get_user_stats(self) -> dict:
        """Obtains a user's stats for a specific app, includes only completed achievements
        along with app specific information"""
        response = await self.client.request("get", "/ISteamUserStats/GetUserStatsForGame/v2/",
                                             params={"steamid": self.from_user_id, "appid": self.app_id})
        self.player_achievement_statistics.update(response)
        return self.player_achievement_statistics

    async def get_user_achievements(self, language: str = "en") -> dict:
        """Obtains information of the user's achievments in the app

        Args:
            language (str): abbreviated language the achievement names are returned in
        """
        response = await self.client.request("get", "/ISteamUserStats/GetPlayerAchievements/v1/",
                                             params={"steamid": self.from_user_id, "appid": self.app_id,
                                                     "l": language})
        self.user_achievements.update(response)
        return self.user_achievements

    async def get_info_from_shop(self) -> 'Game':
        game = await self.client.get_app_details(app_id=self.app_id)
        self.apply_app_details(game)

        if dlc_ids := game.get('dlc') or []:
            dlc_details = await asyncio.gather(*(self.client.get_app_details(app_id=dlc_id) for dlc_id in dlc_ids))
            self.dlc = [Game.from_app_details(details, self.client, self.from_user_id)
                        for details in dlc_details if details]
        return self

    async def get_all_info(self, language: str = "en"):
        await asyncio.gather(
            self.get_info_from_shop(),
            self.get_user_achievements(language),
            self.get_user_stats(),
        )
        return self
