from crud.base import CrudBase
from models.module import RedirectorC2
from models.module import TeamServer


class CrudModule(CrudBase):
    ...


crud_team_server = CrudModule(TeamServer)
crud_redirector = CrudModule(RedirectorC2)
