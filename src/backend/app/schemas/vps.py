from typing import List
from typing import Optional
from typing import Union

from app.models.vps import VpsStatus
from app.schemas.base import APIModel
from app.schemas.base import BasePagination
from app.schemas.base import BaseSchema
from app.schemas.base import BaseSuccessfulResponseModel


class VpsSshKeySchema(APIModel):
    name: str
    public_key: str
    private_key: str = None
    isp_id: int
    ssh_key_id: Optional[str]
    date_created: Optional[str]
    fingerprint: Optional[str]


class VpsSpecPlanSchema(APIModel):
    name: str
    plan_code: Union[str, int]
    region_codes: List = None
    bandwidth: float
    ram: int
    vcpu: int
    disk: int
    price_monthly: float = None
    price_hourly: float = None
    price_yearly: float = None


class VpsSpecRegionSchema(APIModel):
    name: str
    region_code: Union[str, int]
    features: List[str] = None
    plan_codes: List[Union[str, int]] = []


class VpsSpecOsSchema(APIModel):
    name: str
    os_code: Union[str, int]
    region_codes: List[Union[str, int]] = []


class VpsSpecSchema(APIModel):
    region: List[VpsSpecRegionSchema] = []
    plan: List[VpsSpecPlanSchema] = []
    os: List[VpsSpecOsSchema] = []


class VpsSpecResponse(BaseSuccessfulResponseModel):
    result: VpsSpecSchema


class VpsCreateSchema(APIModel):
    hostname: str
    isp_id: int
    region_code: str
    os_code: str
    plan_code: str
    ssh_keys: Optional[List[str]]
    status: int = VpsStatus.init
    remark: str = None


class VpsItemSchema(BaseSchema):
    isp_id: int
    ip: Union[int, str, None]
    server_id: Optional[int]
    hostname: str
    os: Optional[str]
    plan: Optional[str]
    region: Optional[str]
    status: int
    status_name: str
    status_msg: Optional[str]
    isp_provider_name: str


class VpsItemResponse(BaseSuccessfulResponseModel):
    result: VpsItemSchema


class VpsPaginationSchema(BasePagination):
    items: Optional[List[VpsItemSchema]]


class VpsPaginationResponse(BaseSuccessfulResponseModel):
    result: VpsPaginationSchema


class VpsSshKeyResponseSchema(BaseSuccessfulResponseModel):
    result: List[VpsSshKeySchema]
