import enum

from sqlalchemy import BigInteger
from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import Text
from sqlalchemy import orm
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.dialects.postgresql import ARRAY

from app.db.base import BaseModel
from utils.tools import int2ip
from utils.tools import ip2int


class VpsStatus(int, enum.Enum):
    init = 1
    running = 2
    used = 3
    error = 4


class Vps(BaseModel):
    isp_id = Column(Integer, nullable=False)
    ssh_keys = Column(ARRAY(String), nullable=True)
    raw_ip = Column(BigInteger, nullable=True)
    server_id = Column(Integer, nullable=True)
    hostname = Column(String(64), nullable=False)
    os = Column(String(100), nullable=True)
    plan = Column(String(500), nullable=True)
    region = Column(String(100), nullable=True)
    status = Column(Integer, nullable=False)
    status_msg = Column(Text, nullable=True)
    team_servers = orm.relationship(
        "TeamServer",
        primaryjoin='Vps.id == TeamServer.vps_id',
        foreign_keys='TeamServer.vps_id',
        backref=orm.backref('vps', single_parent=True)
    )
    redirector_c2s = orm.relationship(
        "RedirectorC2",
        primaryjoin='Vps.id == RedirectorC2.vps_id',
        foreign_keys='RedirectorC2.vps_id',
        backref=orm.backref('vps', single_parent=True)
    )
    smtp_servers = orm.relationship(
        "SmtpServer",
        primaryjoin='Vps.id == SmtpServer.vps_id',
        foreign_keys='SmtpServer.vps_id',
        backref=orm.backref('vps', single_parent=True)
    )

    @hybrid_property
    def status_name(self) -> str:
        return VpsStatus(self.status).name

    @hybrid_property
    def ip(self):
        return int2ip(self.raw_ip) if self.raw_ip else None

    @ip.setter
    def ip(self, ip_str: str):
        self.raw_ip = ip2int(ip_str)

    @hybrid_property
    def isp_provider_name(self):
        return self.isp.provider_name

    def __str__(self):
        return f"<Vps host:{self.hostname} status: {self.status_name}>"
