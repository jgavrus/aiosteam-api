from pydantic import BaseModel, model_validator


class Badge(BaseModel):
    """One earned badge. Game badges also carry the app they belong to and their border colour;
    the Steam-wide ones (years of service, sale badges) do not."""

    badge_id: int | None = None
    level: int | None = None
    completion_time: int | None = None
    xp: int | None = None
    scarcity: int | None = None
    app_id: int | None = None
    community_item_id: int | None = None
    border_color: int | None = None

    @model_validator(mode='before')
    def normalize_steam_keys(cls, inp: dict):
        """Renames only the keys that are there, so a Badge can also be rebuilt from its own dump"""
        if not isinstance(inp, dict):
            return inp

        for steam_key, field in (('badgeid', 'badge_id'), ('appid', 'app_id'),
                                 ('communityitemid', 'community_item_id')):
            if steam_key in inp:
                inp[field] = inp.pop(steam_key)

        return inp


class Badges(BaseModel):
    """The badge page of a player. Everything defaults, because Steam answers a profile that hides
    its badges with an empty object rather than an error."""

    badges: list[Badge] = []
    player_xp: int | None = None
    player_level: int | None = None
    player_xp_needed_to_level_up: int | None = None
    player_xp_needed_current_level: int | None = None

    @property
    def xp_into_current_level(self) -> int | None:
        """How much of the current level is done, in XP"""
        if self.player_xp is None or self.player_xp_needed_current_level is None:
            return None
        return self.player_xp - self.player_xp_needed_current_level
