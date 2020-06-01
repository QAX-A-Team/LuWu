from datetime import timedelta

from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from sqlalchemy.orm import Session
from starlette import status

from app import crud
from app.api.utils.db import get_db
from app.core import config
from app.core.jwt import create_access_token
from app.schemas.token import AccessTokenResponse
from app.schemas.user import UserLogin

router = APIRouter()


@router.post("/login/access-token", response_model=AccessTokenResponse)
def create_user_access_token(db: Session = Depends(get_db), *, user: UserLogin):
    user = crud.user.authenticate(
        db, username=user.username, password=user.password
    )

    if not user or not crud.user.is_active(user):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect user")

    access_token_expires = timedelta(minutes=config.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token_result = {
        "access_token": create_access_token(
            data={"user_id": user.id}, expires_delta=access_token_expires
        ),
        "token_type": "bearer",
        "expires_in": access_token_expires.total_seconds()
    }
    return dict(result=access_token_result)
