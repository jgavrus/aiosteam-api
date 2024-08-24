from typing import Any, Dict, Optional

from pydantic import BaseModel, model_validator


class LastPlayedGame(BaseModel):
    app_id: int
    name: str
    playtime_two_weeks: int
    playtime_forever: int
    img_icon_url: str

    @model_validator(mode='before')
    def create_avatar_field(cls, inp: dict):
        inp["playtime_two_weeks"] = inp.pop('playtime_2weeks', None)
        inp["app_id"] = inp.pop('appid')

        return inp


class LastPlayedGames(BaseModel):
    games: Dict[int, LastPlayedGame]

    @model_validator(mode='before')
    def create_avatar_field(cls, inp: list):
        new_inp = {}
        for game in inp:
            game = LastPlayedGame.model_validate(game)
            new_inp[game.app_id] = game

        return {"games": new_inp}


class OwnedGame(LastPlayedGame):
    playtime_two_weeks: Optional[int]


class OwnedGames(BaseModel):
    games: Dict[int, OwnedGame]

    @model_validator(mode='before')
    def create_avatar_field(cls, inp: list):
        new_inp = {}
        for game in inp:
            game = OwnedGame.model_validate(game)
            new_inp[game.app_id] = game

        return {"games": new_inp}
