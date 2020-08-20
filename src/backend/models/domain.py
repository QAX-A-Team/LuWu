from datetime import datetime
from typing import Type
from typing import Union

from sqlalchemy import Boolean
from sqlalchemy import Column
from sqlalchemy import DateTime
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import orm
from sqlalchemy.ext.hybrid import hybrid_property

from db.base import BaseModel
from utils.isp import BaseDomainIsp


class Domain(BaseModel):
    isp_id = Column(Integer, nullable=False)
    domain = Column(String(100), nullable=False)
    name_server = Column(String(200), nullable=True)
    status = Column(Boolean, nullable=False, default=False)
    dns_records = orm.relationship(
        'DomainDnsRecord',
        primaryjoin='Domain.id == DomainDnsRecord.domain_id',
        foreign_keys='DomainDnsRecord.domain_id',
        uselist=True,
        backref=orm.backref('domain', single_parent=True)
    )
    redirector_c2s = orm.relationship(
        'RedirectorC2',
        primaryjoin='Domain.id == RedirectorC2.domain_id',
        foreign_keys='RedirectorC2.domain_id',
        uselist=False,
        backref=orm.backref('domain', single_parent=True)
    )
    smtp_servers = orm.relationship(
        'SmtpServer',
        primaryjoin='Domain.id == SmtpServer.domain_id',
        foreign_keys='SmtpServer.domain_id',
        uselist=False,
        backref=orm.backref('domain', single_parent=True)
    )
    tasks = orm.relationship(
        'Task',
        primaryjoin='Domain.id == Task.domain_id',
        foreign_keys='Task.domain_id',
        uselist=False,
        backref=orm.backref('domain', single_parent=True)
    )
    domain_health = orm.relationship(
        'DomainHealth',
        primaryjoin='Domain.id == DomainHealth.domain_id',
        foreign_keys='DomainHealth.domain_id',
        uselist=True,
        backref=orm.backref('domain', single_parent=True)
    )

    @hybrid_property
    def provider_name(self) -> str:
        return self.isp.provider_name

    @hybrid_property
    def isp_instance(self) -> Union[Type[BaseDomainIsp], None]:
        return self.isp.isp_instance

    def __str__(self):
        return f"<Domain {self.domain}>"


class DomainDnsRecord(BaseModel):
    domain_id = Column(Integer, nullable=False)
    record_id = Column(String(50), nullable=False)
    type = Column(String(10), nullable=False)
    host = Column(String(100), nullable=False)
    value = Column(String(100), nullable=False)
    ttl = Column(String(15), nullable=False)
    distance = Column(String(15), nullable=False)

    def __str__(self):
        return f"<DomainDnsRecord {self.host}>"


class DomainHealth(BaseModel):
    domain_id = Column(Integer, nullable=False)
    task_id = Column(Integer, nullable=False)
    host = Column(String(100), nullable=False)
    talos = Column(String(500), nullable=True)
    xforce = Column(String(500), nullable=True)
    opendns = Column(String(500), nullable=True)
    bluecoat = Column(String(500), nullable=True)
    mxtoolbox = Column(String(500), nullable=True)
    trendmicro = Column(String(500), nullable=True)
    fortiguard = Column(String(500), nullable=True)
    health = Column(String(500), nullable=True)
    explanation = Column(String(500), nullable=True)
    health_dns = Column(String(500), nullable=True)
    last_time = Column(DateTime, nullable=True, default=datetime.utcnow)

    def __str__(self):
        return f"<DomainHealth {self.task_id}>"


class Task(BaseModel):
    domain_id = Column(Integer, nullable=False)
    name = Column(String(100), nullable=False)
    interval = Column(Integer, nullable=True)
    active = Column(Boolean, nullable=True, default=True)
    domain_healths = orm.relationship(
        "DomainHealth",
        primaryjoin='Task.id == DomainHealth.task_id',
        foreign_keys='DomainHealth.task_id',
        backref=orm.backref('task', single_parent=True)
    )

    @hybrid_property
    def domain_name(self):
        return self.domain.domain if self.domain else None

    @hybrid_property
    def health_records(self):
        return self.domain_healths if self.domain_healths else []

    def __str__(self):
        return f"<Task {self.domain_id}>"


class DomainGrow(BaseModel):
    isp_id = Column(Integer, nullable=False)
    domain_id = Column(Integer, nullable=False)
    template_id = Column(Integer, nullable=False)
    vps_id = Column(Integer, nullable=False)

    isp = orm.relationship(
        'Isp',
        primaryjoin='DomainGrow.isp_id == Isp.id',
        foreign_keys='Isp.id',
        uselist=False,
        backref=orm.backref('domain_grow')
    )
    domain = orm.relationship(
        'Domain',
        primaryjoin='DomainGrow.domain_id == Domain.id',
        foreign_keys='Domain.id',
        uselist=False,
        backref=orm.backref('domain_grow')
    )
    vps = orm.relationship(
        'Vps',
        primaryjoin='DomainGrow.vps_id == Vps.id',
        foreign_keys='Vps.id',
        uselist=False,
        backref=orm.backref('domain_grow')
    )
    template = orm.relationship(
        'SiteTemplate',
        primaryjoin='DomainGrow.template_id == SiteTemplate.id',
        foreign_keys='SiteTemplate.id',
        uselist=False,
        backref=orm.backref('domain_grow')
    )

    @hybrid_property
    def provider_name(self):
        return self.isp.provider_name

    @hybrid_property
    def template_name(self):
        return self.template.name

    @hybrid_property
    def domain_name(self):
        return self.domain.domain

    @hybrid_property
    def vps_hostname(self):
        return self.vps.hostname

    @hybrid_property
    def vps_ip(self):
        return self.vps.ip

    @hybrid_property
    def health_records(self):
        return self.domain.domain_healths if self.domain.domain_healths else []

    def __str__(self):
        return f"<DomainGrow {self.domain_id}>"
