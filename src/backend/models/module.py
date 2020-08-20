import enum

from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import Text
from sqlalchemy import orm
from sqlalchemy.ext.hybrid import hybrid_property

from db.base import BaseModel


class RedirectorBeaconType(int, enum.Enum):
    http = 1
    https = 2
    dns = 3


class TeamServer(BaseModel):
    vps_id = Column(Integer, nullable=False)
    c2_profile_id = Column(Integer, nullable=True)
    kill_date = Column(String(15), nullable=True)
    port = Column(Integer, nullable=False)
    password = Column(String(32), nullable=True)
    cs_download_url = Column(Text, nullable=False)
    zip_password = Column(Text, nullable=True)
    redirector_c2s = orm.relationship(
        "RedirectorC2",
        primaryjoin='TeamServer.id == RedirectorC2.team_server_id',
        foreign_keys='RedirectorC2.team_server_id',
        backref=orm.backref('team_server', single_parent=True)
    )

    @hybrid_property
    def ip(self):
        return self.vps.ip

    @hybrid_property
    def hostname(self):
        return self.vps.hostname

    @hybrid_property
    def isp_provider_name(self):
        return self.vps.isp.provider_name

    @hybrid_property
    def c2_profile_name(self):
        return self.c2_profile.name

    @hybrid_property
    def cs_conn_url(self):
        return f"https://{self.ip}:{self.port}"

    def __str__(self):
        return f"<TeamServer {self.ip}>"


class RedirectorC2(BaseModel):
    vps_id = Column(Integer, nullable=False)
    domain_id = Column(Integer, nullable=False)
    team_server_id = Column(Integer, nullable=False)
    listener_port = Column(Integer, nullable=False)
    beacon_type = Column(Integer, nullable=False)
    redirect_domain = Column(String(100), nullable=False)

    @hybrid_property
    def beacon_type_name(self):
        return RedirectorBeaconType(self.beacon_type).name

    @hybrid_property
    def ip(self):
        return self.vps.ip

    @hybrid_property
    def domain_name(self):
        return self.domain.domain

    @hybrid_property
    def hostname(self):
        return self.vps.hostname

    def __str__(self):
        return f"<RedirectorC2 {self.beacon_type}>"


class SmtpServer(BaseModel):
    vps_id = Column(Integer, nullable=False)
    domain_id = Column(Integer, nullable=False)
    name = Column(String(64), unique=True, nullable=False)
    ip = Column(String(15), nullable=False)
    admin_mail = Column(String(100), nullable=False)
    admin_password = Column(String(100), nullable=False)
    mail_users = orm.relationship(
        "MailUser",
        primaryjoin='SmtpServer.id == MailUser.smtp_server_id',
        foreign_keys='MailUser.smtp_server_id',
        backref=orm.backref('smtp_server', single_parent=True)
    )

    def __str__(self):
        return f"<SmtpServer {self.name}>"


class MailUser(BaseModel):
    smtp_server_id = Column(Integer, nullable=False)
    mail = Column(String(100), nullable=False)
    password = Column(String(100), nullable=False)

    def __str__(self):
        return f"<MailUser {self.mail}>"
