from sqlalchemy.orm import Query
from sqlalchemy.orm import Session

from crud.base import CrudBase
from models.domain import Domain
from models.domain import DomainDnsRecord
from models.domain import DomainGrow
from models.domain import DomainHealth
from models.domain import Task


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
