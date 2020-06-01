from datetime import datetime
from functools import partial
from typing import Any
from typing import Optional
from typing import Union

from pydantic import BaseConfig
from pydantic import BaseModel
from pydantic import Field
from pydantic import validator

from app.core import config
from utils.tools import snake2camel


class APIModel(BaseModel):
    """
    Intended for use as a base class for externally-facing models.
    Any models that inherit from this class will:
    * accept fields using snake_case or camelCase keys
    * use camelCase keys in the generated OpenAPI spec
    * have orm_mode on by default
        * Because of this, FastAPI will automatically attempt to parse returned orm instances into the model
    """

    class Config(BaseConfig):
        orm_mode = True
        allow_population_by_field_name = True
        alias_generator = partial(snake2camel, start_lower=True)


class BaseSchema(APIModel):
    id: Optional[int] = Field(None, alias='id')
    created_on: Optional[datetime]
    updated_on: Optional[datetime]
    remark: Optional[str]


class BasePaginationQuerySchema(APIModel):
    page: Optional[int] = 1
    per_page: Optional[int] = config.PAGINATION_PER_PAGE
    count: Optional[bool] = True
    query_all: Optional[bool] = False

    @validator('page')
    def validate_page(cls, page: int) -> int:
        return page if page > 0 else 1

    class Config:
        orm_mode = True


class BasePagination(APIModel):
    page: int = 1
    prev_num: Union[int, None] = 1
    has_prev: bool = False
    has_next: bool = False
    total: Union[int, None] = 0
    items: Optional[list]

    class Config:
        orm_mode = True


class BaseResponseModel(APIModel):
    success: bool
    errors: list = None
    result: Any


class BaseSuccessfulResponseModel(BaseResponseModel):
    success: bool = True


class BaseFailedResponseModel(BaseResponseModel):
    success: bool = False


class BaseCrudStatusSchema(APIModel):
    status: bool


class BaseCrudStatusResponse(BaseSuccessfulResponseModel):
    result: BaseCrudStatusSchema


class BaseTaskRunningSchema(APIModel):
    task_id: str


class TaskResponse(BaseSuccessfulResponseModel):
    result: BaseTaskRunningSchema
