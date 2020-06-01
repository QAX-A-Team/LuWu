from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app import crud
from app.api.utils.db import get_db
from app.api.utils.security import get_current_active_user
from app.models.user import User as DBUser
from app.schemas.user import UserResponse

router = APIRouter()


@router.get("/me", response_model=UserResponse)
def read_user_me(
    current_user: DBUser = Depends(get_current_active_user),
):
    """
    Get current user.
    """
    result = dict(result=current_user)
    return result


@router.get("/{user_id}", response_model=UserResponse)
def read_user_by_id(
    user_id: int,
    current_user: DBUser = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Get a specific user by id.
    """
    user = crud.user.get(db, id=user_id)
    if user == current_user:
        return user
    if not crud.user.is_superuser(current_user):
        raise HTTPException(
            status_code=400, detail="The user doesn't have enough privileges"
        )
    result = dict(result=user)

    return result

