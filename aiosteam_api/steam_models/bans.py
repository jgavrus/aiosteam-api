from pydantic import BaseModel, model_validator

# GetPlayerBans is the one Steam endpoint that answers in PascalCase, so its keys need a real map
# rather than the separator-stripping trick the other models use.
_STEAM_KEYS = {
    "SteamId": "steam_id",
    "CommunityBanned": "community_banned",
    "VACBanned": "vac_banned",
    "NumberOfVACBans": "number_of_vac_bans",
    "DaysSinceLastBan": "days_since_last_ban",
    "NumberOfGameBans": "number_of_game_bans",
    "EconomyBan": "economy_ban",
}


class PlayerBans(BaseModel):
    """The ban record of one player.

    `days_since_last_ban` is 0 both for a player who has never been banned and for one banned today,
    so read it together with the counters. `economy_ban` is "none", "probation" or "banned".
    """

    steam_id: int | None = None
    community_banned: bool | None = None
    vac_banned: bool | None = None
    number_of_vac_bans: int | None = None
    days_since_last_ban: int | None = None
    number_of_game_bans: int | None = None
    economy_ban: str | None = None

    @model_validator(mode='before')
    def normalize_steam_keys(cls, inp: dict):
        """Renames only the keys that are there, so a PlayerBans can also be rebuilt from its own dump"""
        if not isinstance(inp, dict):
            return inp

        return {_STEAM_KEYS.get(key, key): value for key, value in inp.items()}

    @property
    def is_clean(self) -> bool:
        """True when the account carries no ban of any kind"""
        return not (self.vac_banned or self.community_banned or self.number_of_vac_bans
                    or self.number_of_game_bans or (self.economy_ban or "none") != "none")
