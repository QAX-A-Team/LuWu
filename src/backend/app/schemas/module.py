from typing import List
from typing import Optional

from app.models.module import RedirectorBeaconType
from app.schemas.base import BasePagination
from app.schemas.base import BaseSchema
from app.schemas.base import BaseSuccessfulResponseModel
from app.schemas.base import APIModel


class TeamServerCreateSchema(APIModel):
    port: int = 9990
    password: Optional[str]
    c2_profile_id: Optional[int]
    vps_id: int
    kill_date: Optional[str]
    remark: Optional[str] = None
    cs_download_url: str
    zip_password: Optional[str]


class TeamServerItemSchema(BaseSchema):
    port: Optional[int]
    password: Optional[str]
    c2_profile_id: Optional[int]
    vps_id: int
    kill_date: Optional[str]
    hostname: str
    ip: Optional[str]
    isp_provider_name: str
    c2_profile_name: Optional[str]


class TeamServerItemResponse(BaseSuccessfulResponseModel):
    result: TeamServerItemSchema


class TeamServerPaginationSchema(BasePagination):
    items: Optional[List[TeamServerItemSchema]]


class TeamServerPaginationResponse(BaseSuccessfulResponseModel):
    result: TeamServerPaginationSchema


class RedirectorCreateSchema(APIModel):
    beacon_type: RedirectorBeaconType
    team_server_id: int
    listener_port: int
    redirect_domain: str
    remark: Optional[str]
    vps_id: int
    domain_id: int


class RedirectorItemSchema(BaseSchema, RedirectorCreateSchema):
    beacon_type_name: str
    hostname: str
    domain_name: str
    ip: str


class RedirectorPaginationSchema(BasePagination):
    items: Optional[List[RedirectorItemSchema]]


class RedirectorPaginationResponse(BaseSuccessfulResponseModel):
    result: RedirectorPaginationSchema
