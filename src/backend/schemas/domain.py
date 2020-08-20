from datetime import datetime
from typing import List
from typing import Optional

from schemas.base import APIModel
from schemas.base import BasePagination
from schemas.base import BaseSchema
from schemas.base import BaseSuccessfulResponseModel


class DomainDnsRecordItem(BaseSchema):
    domain_id: int
    record_id: str
    type: str
    host: str
    value: str
    ttl: int
    distance: str


class DomainBase(BaseSchema):
    domain: str


class DomainCreate(DomainBase):
    isp_id: int


class DomainItem(DomainBase):
    provider_name: str
    name_server: Optional[str]
    dns_records: Optional[List[DomainDnsRecordItem]]
    status: bool


class DomainPagination(BasePagination):
    items: Optional[List[DomainItem]]


class DomainPaginationResponse(BaseSuccessfulResponseModel):
    result: DomainPagination


class PurchasableDomainQuerySchema(APIModel):
    isp_id: int
    domain: str


class PurchasableDomainItemSchema(APIModel):
    text: str
    price: Optional[float]
    purchasable: bool


class PurchasableDomainResponse(BaseSuccessfulResponseModel):
    result: Optional[List[PurchasableDomainItemSchema]]


class PurchaseDomainSchema(APIModel):
    price: Optional[float]
    domain: str
    isp_id: int
    provider_name: str


class VerifyDomainSchema(APIModel):
    domain: str
    vt_token: Optional[str]


class DomainMonitorSchema(APIModel):
    domain_id: int
    name: str
    interval: int
    remark: Optional[str] = None


class DomainHealthItem(BaseSchema):
    domain_id: int
    task_id: int
    host: str
    talos: str
    xforce: str
    opendns: str
    bluecoat: str
    mxtoolbox: str
    trendmicro: str
    fortiguard: str
    health: str
    explanation: str
    health_dns: str
    last_time: Optional[datetime]


class DomainMonitorTaskItem(BaseSchema):
    domain_id: int
    domain_name: Optional[str]
    name: str
    interval: int
    active: bool
    health_records: Optional[List[DomainHealthItem]]


class DomainMonitorTaskResponse(BaseSuccessfulResponseModel):
    result: DomainMonitorTaskItem


class DomainMonitorPagination(BasePagination):
    items: Optional[List[DomainMonitorTaskItem]]


class DomainMonitorPaginationResponse(BaseSuccessfulResponseModel):
    result: DomainMonitorPagination


class DomainGrowCreate(APIModel):
    isp_id: int
    vps_id: int
    domain_id: int
    template_id: int
    remark: Optional[str] = None


class DomainGrowItem(DomainGrowCreate, BaseSchema):
    provider_name: str
    template_name: str
    domain_name: Optional[str]
    vps_hostname: Optional[str]
    vps_ip: Optional[str]
    health_records: Optional[List[DomainHealthItem]]


class DomainGrowPagination(BasePagination):
    items: Optional[List[DomainGrowItem]]


class DomainGrowPaginationResponse(BaseSuccessfulResponseModel):
    result: DomainGrowPagination


class DomainGrowCreateSchema(APIModel):
    isp_id: int
    domain_id: int
    template_id: int
    vps_id: int
