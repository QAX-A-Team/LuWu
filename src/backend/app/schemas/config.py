from enum import Enum
from typing import List
from typing import Optional
from typing import Union

from pydantic import validator

from app.models.config import DomainIsp
from app.models.config import IspType
from app.models.config import VpsIsp
from app.schemas.base import APIModel
from app.schemas.base import BasePagination
from app.schemas.base import BasePaginationQuerySchema
from app.schemas.base import BaseSchema
from app.schemas.base import BaseSuccessfulResponseModel


class IspProvider(APIModel):
    name: str
    code: int


class IspAvailable(APIModel):
    domain: Optional[List[IspProvider]] = None
    vps: Optional[List[IspProvider]] = None


class IspAvailableResponse(BaseSuccessfulResponseModel):
    result: IspAvailable


class IspApiKey(BaseSchema):
    api_key: Optional[str] = None
    is_test: Optional[bool] = None


class IspBase(IspApiKey, BaseSchema):
    type: Optional[IspType] = None
    provider: Optional[Union[DomainIsp, VpsIsp]] = None


class IspItem(IspBase):
    isp_name: Optional[str]
    provider_name: Optional[str]
    isp_api_url: Optional[Union[str, None]]


class IspItemResponse(BaseSuccessfulResponseModel):
    result: IspItem


class IspPaginationQuerySchema(BasePaginationQuerySchema):
    type: Optional[Union[int, IspType]] = None

    @validator('type')
    def transform_enum(cls, v: Union[int, IspType]) -> int:
        if isinstance(v, Enum):
            v = v.value
        assert v in [isp.value for isp in IspType]
        return v

    class Config:
        orm_mode = True


class IspPagination(BasePagination):
    items: Optional[List[IspItem]]


class IspPaginationResponse(BaseSuccessfulResponseModel):
    result: IspPagination


class IspCreate(IspBase):
    type: IspType
    provider: Optional[Union[DomainIsp, VpsIsp]] = None
    api_key: Optional[str] = None
    is_test: Optional[bool] = None


class DomainIspCreate(IspCreate):
    type = IspType.domain


class VpsIspCreate(IspCreate):
    type = IspType.vps


class IspUpdate(IspBase):
    type: IspType
    provider: Optional[Union[DomainIsp, VpsIsp]] = None


class C2ProfileBaseSchema(BaseSchema):
    name: str


class C2ProfileCreate(C2ProfileBaseSchema):
    profile_name: str
    profile_content: bytes


class C2ProfileCreateResponse(BaseSuccessfulResponseModel):
    result: C2ProfileCreate


class C2ProfileUpdate(C2ProfileBaseSchema):
    name: str


class C2ProfileItem(C2ProfileBaseSchema):
    profile_name: str
    profile_content: bytes


class C2ProfileItemResponse(BaseSuccessfulResponseModel):
    result: C2ProfileItem


class C2Pagination(BasePagination):
    items: Optional[List[C2ProfileItem]]


class C2PaginationResponse(BaseSuccessfulResponseModel):
    result: C2Pagination


class SiteTemplateItem(BaseSchema):
    name: str
    zip_file_name: str
    zip_file_size: str


class SiteTemplateUpdateSchema(APIModel):
    id: int
    name: str
    remark: Optional[str]


class SiteTemplateItemResponse(BaseSuccessfulResponseModel):
    result: SiteTemplateItem


class SiteTemplatePagination(BasePagination):
    items: Optional[List[SiteTemplateItem]]


class SiteTemplatePaginationResponse(BaseSuccessfulResponseModel):
    result: SiteTemplatePagination


class SshConfig(BaseSchema):
    private_key: str
    public_key: str


class SshConfigResponse(BaseSuccessfulResponseModel):
    result: Optional[SshConfig]
