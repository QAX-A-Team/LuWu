from app.core import config
from app.crud.crud_user import user
from app.schemas.user import UserCreate

# make sure all SQL Alchemy models are imported before initializing DB
# otherwise, SQL Alchemy might fail to initialize relationships properly
# for more details: https://github.com/tiangolo/full-stack-fastapi-postgresql/issues/28
from app.db import base


def init_db(db_session):
    init_user = user.get_by_username(
        db_session, username=config.FIRST_SUPERUSER_USERNAME
    )
    if not init_user:
        user_in = UserCreate(
            username=config.FIRST_SUPERUSER_USERNAME,
            email=config.FIRST_SUPERUSER_EMAIL,
            password=config.FIRST_SUPERUSER_PASSWORD,
            is_superuser=True,
        )
        init_user = user.create(db_session, obj_in=user_in)
