from pydantic import BaseModel, model_validator


class Badge(BaseModel):
    badge_id: int
    level: int
    completion_time: int
    xp: int
    scarcity: int

    @model_validator(mode='before')
    def reformat_badge_id(cls, inp: dict):
        inp['badge_id'] = inp.pop('badgeid')
        return inp


class Badges(BaseModel):
    badges: list[Badge]
    player_xp: int
    player_level: int
    player_xp_needed_to_level_up: int
    player_xp_needed_current_level: int
