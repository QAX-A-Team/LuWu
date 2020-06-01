from app.schemas.base import APIModel
from app.schemas.base import BaseSuccessfulResponseModel


class Token(APIModel):
    access_token: str
    token_type: str
    expires_in: int


class TokenPayload(APIModel):
    user_id: int = None


class AccessTokenResponse(BaseSuccessfulResponseModel):
    result: Token
