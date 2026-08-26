
from pydantic import BaseModel, model_validator, ConfigDict

from aiosteam_api.clients.requests_client import RequestsClient
from aiosteam_api.steam_models.games import Game


class WishlistItem(BaseModel):
    """One entry of a user's wishlist.

    IWishlistService only returns the app id and when/how the user wishlisted it, so this is not a Game.
    Call get_game() to pay for the extra store request and get the full app details.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)
    client: RequestsClient
    app_id: int
    priority: int | None = None
    date_added: int | None = None
    from_user_id: int | None = None

    @model_validator(mode='before')
    def normalize_steam_keys(cls, inp: dict):
        if not isinstance(inp, dict):
            return inp

        app_id = inp.pop('appid', None)
        if app_id is not None:
            inp['app_id'] = app_id

        return inp

    async def get_game(self, country: str = "US", filters: str | None = None) -> Game:
        """Fetches the store info of the wishlisted app

        As with Game.get_info_from_shop, `filters=None` asks for the whole payload — a wishlist is
        mostly read for the price, which the store's "basic" filter does not include, and `country`
        picks the store whose currency that price is in.
        """
        details = await self.client.get_app_details(app_id=self.app_id, country=country, filters=filters)
        return Game.from_app_details(details, self.client, self.from_user_id)
