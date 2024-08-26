from typing import Optional

from pydantic import BaseModel, model_validator, ConfigDict

from aiosteam_api.clients.requests_client import RequestsClient


class Game(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    client: RequestsClient
    app_id: int
    name: str
    playtime_forever: Optional[int] = None
    img_icon_url: Optional[str] = None
    playtime_two_weeks: Optional[int] = None
    user_stats: Optional[dict] = {}
    user_achievements: Optional[dict] = {}
    from_user_id: Optional[int] = None
    required_age: Optional[int] = None
    is_free: Optional[bool] = None
    dlc: Optional[list['Game']] = None
    detailed_description: Optional[str] = None
    about_the_game: Optional[str] = None
    short_description: Optional[str] = None
    supported_languages: Optional[dict[str, str]] = None
    header_image: Optional[str] = None
    capsule_image: Optional[str] = None
    capsule_imagev5: Optional[str] = None
    website: Optional[str] = None
    pc_requirements: Optional[dict | list] = None
    mac_requirements: Optional[dict | list] = None
    linux_requirements: Optional[dict | list] = None
    player_achievement_statistics: Optional[dict] = {}

    @model_validator(mode='before')
    def create_avatar_field(cls, inp: dict):
        inp["playtime_two_weeks"] = inp.pop('playtime_2weeks', None)
        inp["app_id"] = inp.pop('appid', None) or inp.pop('steam_appid', None)

        return inp

    @staticmethod
    def parse_supported_languages(text) -> dict[str, str]:
        text = text.strip('languages with full audio support')
        text = text.split(', ')
        result = {}
        for row in text:
            if len(row.split('<')) >= 2:
                name = row.split('<')[0]
                result[name] = 'full'
            else:
                result[row] = 'text'
        return result

    async def get_user_stats(self) -> dict:
        """Obtains a user's stats for a specific app, includes only completed achievements
        along with app specific information"""
        response = await self.client.request("get", "/ISteamUserStats/GetUserStatsForGame/v2/",
                                             params={"steamid": self.from_user_id, "appid": self.app_id})
        self.player_achievement_statistics.update(response)
        return self.player_achievement_statistics

    async def get_user_achievements(self) -> dict:
        """Obtains information of the user's achievments in the app
        """
        response = await self.client.request("get", "/ISteamUserStats/GetPlayerAchievements/v1/",
                                             params={"steamid": self.from_user_id, "appid": self.app_id})
        self.user_achievements.update(response)
        return self.user_achievements

    async def get_info_from_shop(self) -> 'Game':
        game = await self.client.get_app_details(app_id=self.app_id)
        self.required_age = int(game.get('required_age'))
        self.is_free = game.get('is_free')
        self.detailed_description = game.get('detailed_description')
        self.about_the_game = game.get('about_the_game')
        self.short_description = game.get('short_description')
        self.supported_languages = self.parse_supported_languages(game.get('supported_languages', ''))
        self.pc_requirements = game.get('pc_requirements')
        self.mac_requirements = game.get('mac_requirements')
        self.linux_requirements = game.get('linux_requirements')
        self.header_image = game.get('header_image')
        self.capsule_image = game.get('capsule_image')
        self.capsule_imagev5 = game.get('capsule_imagev5')
        if dlcs := game.get('dlc', []):
            dlc = []
            for row in dlcs:
                game_dlc = await self.client.get_app_details(app_id=row)
                game_dlc['client'] = self.client
                game_dlc['supported_languages'] = self.parse_supported_languages(
                    game_dlc.get('supported_languages', ''))
                parsed_dlc = Game.model_validate(game_dlc)
                dlc.append(parsed_dlc)
            self.dlc = dlc
        return self

    async def get_all_info(self):
        await self.get_info_from_shop()
        await self.get_user_achievements()
        await self.get_user_stats()
        return self
