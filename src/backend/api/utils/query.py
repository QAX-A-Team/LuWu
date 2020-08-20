from fastapi import Query

from core import config
from models.config import IspType


class PaginationQuery:
    def __init__(
        self,
        page: int = Query(1),
        per_page: int = Query(config.PAGINATION_PER_PAGE, alias='perPage'),
        count: bool = Query(True),
        query_all: bool = Query(False, alias='queryAll'),
    ):
        self.page = page
        self.per_page = per_page
        self.count = count
        self.query_all = query_all


class DomainIspPaginationQuery(PaginationQuery):
    type = IspType.domain.value


class VpsIspPaginationQuery(PaginationQuery):
    type = IspType.vps


class C2PaginationQuery(PaginationQuery):
    ...
