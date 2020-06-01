from sqlalchemy.orm import Query
from sqlalchemy.orm import Session

from app.crud.base import CrudBase
from app.models.domain import Domain
from app.models.domain import DomainDnsRecord
from app.models.domain import DomainGrow
from app.models.domain import DomainHealth
from app.models.domain import Task


class CrudDomain(CrudBase):
    def get_domain_list(self, db_session: Session) -> Query:
        return db_session.query(self.model).all()


class CrudDomainDnsRecord(CrudBase):
    ...


class CrudDomainHealth(CrudBase):
    ...


class CrudTask(CrudBase):
    def get_active_task(self, db_session: Session):
        return self.filter_by(db_session=db_session, active=True)


class CrudDomainGrow(CrudBase):
    ...


crud_domain = CrudDomain(Domain)
crud_domain_dns_record = CrudDomainDnsRecord(DomainDnsRecord)
crud_domain_health = CrudDomainHealth(DomainHealth)
crud_domain_task = CrudTask(Task)
crud_domain_grow = CrudDomainGrow(DomainGrow)
