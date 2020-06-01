from fastapi import APIRouter
from fastapi import Security

from app.api.api_v1.endpoints import config
from app.api.api_v1.endpoints import domains
from app.api.api_v1.endpoints import login
from app.api.api_v1.endpoints import modules
from app.api.api_v1.endpoints import users
from app.api.api_v1.endpoints import vps
from app.api.utils.security import get_current_user

api_router = APIRouter()
api_router.include_router(login.router, tags=['login'])
api_router.include_router(
    config.router, prefix='/config', tags=['config'], dependencies=[Security(get_current_user)]
)
api_router.include_router(users.router, prefix='/users', tags=['users'])
api_router.include_router(
    vps.router, prefix='/vps', tags=['vps'], dependencies=[Security(get_current_user)]
)
api_router.include_router(
    domains.router, prefix='/domains', tags=['domains'], dependencies=[Security(get_current_user)]
)
api_router.include_router(
    modules.router, prefix='/modules', tags=['modules'], dependencies=[Security(get_current_user)]
)
