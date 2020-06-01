from app.crud.base import CrudBase
from app.models.module import RedirectorC2
from app.models.module import TeamServer


class CrudModule(CrudBase):
    ...


crud_team_server = CrudModule(TeamServer)
crud_redirector = CrudModule(RedirectorC2)
