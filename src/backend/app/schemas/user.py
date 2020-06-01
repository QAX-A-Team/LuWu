from datetime import datetime
from typing import List
from typing import Optional

from app.schemas.base import APIModel
from app.schemas.base import BaseSuccessfulResponseModel


class UserLogin(APIModel):
    username: str
    password: str


class UserBase(APIModel):
    username: Optional[str] = None
    email: Optional[str] = None
    is_active: Optional[bool] = True
    is_superuser: Optional[bool] = False
    login_time: datetime = None


class UserBaseInDB(UserBase):
    id: int = None

    class Config:
        orm_mode = True


# Properties to receive via API on creation
class UserCreate(UserBaseInDB):
    email: str
    password: str


# Properties to receive via API on update
class UserUpdate(UserBaseInDB):
    password: Optional[str] = None


# Additional properties to return via API
class User(UserBaseInDB):
    pass


# Additional properties stored in DB
class UserInDB(UserBaseInDB):
    hashed_password: str


class UserResponse(BaseSuccessfulResponseModel):
    result: User


class UsersResponse(BaseSuccessfulResponseModel):
    result: List[User]
