from typing import Optional, Any

from pydantic import BaseModel, model_validator

from aiosteam.types.badges import Badges
from aiosteam.types.games import LastPlayedGame, OwnedGames, OwnedGame


class UserAvatarModel(BaseModel):
    avatar: str
    avatar_medium: str
    avatar_full: str
    avatar_hash: str


class FriendModel(BaseModel):
    steam_id: int
    community_visibility_state: int
    profile_state: int
    persona_name: str
    profile_url: str
    avatar: UserAvatarModel
    last_logoff: Optional[int]
    persona_state: int
    real_name: Optional[str]
    primary_clan_id: int
    time_created: int
    persona_state_flags: int
    loc_country_code: Optional[str]
    relationship: str
    friend_since: int


class UserModel(BaseModel):
    steam_id: int
    player_lvl: Optional[int]
    community_visibility_state: int
    profile_state: int
    persona_name: str
    profile_url: str
    avatar: UserAvatarModel
    last_logoff: Optional[int]
    persona_state: int
    real_name: Optional[str]
    primary_clan_id: int
    time_created: int
    persona_state_flags: int
    loc_country_code: Optional[str]
    friends: Optional[list[FriendModel]]
    last_played_games: Optional[dict[int, LastPlayedGame]]
    owned_games: Optional[dict[int, OwnedGame]]
    user_badges: Optional[Badges]

    @model_validator(mode='before')
    def create_avatar_field(cls, inp: dict):
        new_inp = {}
        for field in cls.model_fields:
            new_inp[field] = inp.get(field.replace('_', ''))

        new_inp['avatar'] = UserAvatarModel(avatar=inp.pop('avatar'),
                                            avatar_medium=inp.pop('avatarmedium'),
                                            avatar_full=inp.pop('avatarfull'),
                                            avatar_hash=inp.pop('avatarhash'))

        return new_inp

    def __init__(self, **data: Any):
        super().__init__(**data)


class UsersModel(BaseModel):
    users: list[UserModel]
