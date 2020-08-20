import enum
import os
from io import StringIO
from typing import Optional
from typing import Tuple
from typing import Type
from typing import Union

import paramiko
from sqlalchemy import Boolean
from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import LargeBinary
from sqlalchemy import String
from sqlalchemy import Text
from sqlalchemy import orm
from sqlalchemy.ext.hybrid import hybrid_property

from core.config import PROJECT_NAME
from db.base import BaseModel
from models.domain import Domain
from models.module import TeamServer
from utils.isp import BaseIsp
from utils.isp import DigitalOceanIsp
from utils.isp import NameSiloIsp
from utils.isp import TencentCloudIsp
from utils.isp import AliyunIsp
from utils.isp import AlibabaCloudIsp
from utils.isp import VultrIsp
from utils.tools import get_printable_size


class IspType(int, enum.Enum):
    domain = 1
    vps = 2


class DomainIsp(int, enum.Enum):
    namesilo = 1


class VpsIsp(int, enum.Enum):
    vultr = 1
    digitalocean = 2
    tencent = 3
    aliyun = 4
    alibabaCloud = 5


class IspApiKey(BaseModel):
    """
    ISP API Key Model
    """

    api_key = Column(String(100), nullable=False)
    api_id = Column(String(100), nullable=True)
    is_test = Column(Boolean, default=False)
    isp = orm.relationship(
        "Isp",
        primaryjoin="IspApiKey.id == Isp.api_key_id",
        foreign_keys="Isp.api_key_id",
        uselist=False,
        backref=orm.backref(
            "isp_api_key", single_parent=True, cascade="all, delete-orphan"
        ),
    )

    def __str__(self):
        return f"<ISP API KEY {self.api_key}>"


class Isp(BaseModel):
    """
    ISP Data Model
    """

    AVAILABLE_ISP = {IspType.domain: DomainIsp, IspType.vps: VpsIsp}
    ISP_LIB_MAP = {
        (IspType.domain, DomainIsp.namesilo): NameSiloIsp,
        (IspType.vps, VpsIsp.digitalocean): DigitalOceanIsp,
        (IspType.vps, VpsIsp.vultr): VultrIsp,
        (IspType.vps, VpsIsp.tencent): TencentCloudIsp,
        (IspType.vps, VpsIsp.aliyun): AliyunIsp,
        (IspType.vps, VpsIsp.alibabaCloud): AlibabaCloudIsp,
    }

    type = Column(Integer, nullable=False)
    provider = Column(Integer, nullable=False)
    api_key_id = Column(Integer, nullable=False)
    domain = orm.relationship(
        Domain,
        primaryjoin="Isp.id == Domain.isp_id",
        foreign_keys="Domain.isp_id",
        uselist=True,
        cascade="all, delete-orphan",
        backref=orm.backref("isp", single_parent=True),
    )
    vps = orm.relationship(
        "Vps",
        primaryjoin="Isp.id == Vps.isp_id",
        foreign_keys="Vps.isp_id",
        uselist=True,
        backref=orm.backref("isp", single_parent=True),
    )

    def __init__(self, *args, **kwargs):
        inner_attr_map = {
            key: value for key, value in kwargs.items() if hasattr(self, key)
        }
        super().__init__(**inner_attr_map)

        api_id = kwargs.get("api_id")
        api_key = kwargs["api_key"]
        is_test = kwargs["is_test"]
        self.isp_api_key = IspApiKey(api_id=api_id, api_key=api_key, is_test=is_test)

    @hybrid_property
    def isp_name(self) -> str:
        return IspType(self.type).name

    @hybrid_property
    def provider_name(self) -> str:
        return self.AVAILABLE_ISP[IspType(self.type)](self.provider).name

    @hybrid_property
    def api_id(self) -> str:
        return self.isp_api_key.api_id

    @api_id.setter
    def api_id(self, api_id: str) -> None:
        self.isp_api_key.api_id = api_id

    @hybrid_property
    def api_key(self) -> str:
        return self.isp_api_key.api_key

    @api_key.setter
    def api_key(self, api_key: str) -> None:
        self.isp_api_key.api_key = api_key

    @hybrid_property
    def is_test(self) -> bool:
        return self.isp_api_key.is_test

    @is_test.setter
    def is_test(self, is_test: bool) -> None:
        self.isp_api_key.is_test = is_test

    @hybrid_property
    def isp_lib(self) -> Union[Type[BaseIsp], None]:
        return self.ISP_LIB_MAP.get((self.type, self.provider), None)

    @hybrid_property
    def isp_instance(self) -> Union[Type[BaseIsp], None]:
        if self.isp_lib:
            instance = self.isp_lib(
                self.api_key, api_id=self.api_id, is_test=self.is_test
            )
        else:
            instance = None
        return instance

    @hybrid_property
    def isp_api_url(self) -> Optional[str]:
        if self.isp_lib:
            api_url = self.isp_instance.api_url
        else:
            api_url = None

        return api_url

    @hybrid_property
    def is_vps_isp(self) -> bool:
        return self.type == IspType.vps.value

    @classmethod
    def get_available_isp(cls) -> dict:
        return {
            IspType.domain.name: cls.serialise_enum_data(DomainIsp),
            IspType.vps.name: cls.serialise_enum_data(VpsIsp),
        }

    def __str__(self) -> str:
        return f"<ISP {self.isp_name} {self.provider_name}>"


class C2Profile(BaseModel):
    """
    C2 Profile Model
    """

    name = Column(String(64), nullable=False)
    profile_name = Column(String(64), nullable=False)
    profile_content = Column(LargeBinary, nullable=False)
    team_servers = orm.relationship(
        TeamServer,
        primaryjoin="C2Profile.id == TeamServer.c2_profile_id",
        foreign_keys="TeamServer.c2_profile_id",
        backref=orm.backref("c2_profile", single_parent=True),
    )

    def __str__(self) -> str:
        return f"<C2 {self.name} {self.profile_name}>"


class SiteTemplate(BaseModel):
    name = Column(String(64), nullable=False)
    zip_file_name = Column(String(100), nullable=True)
    zip_file_content = Column(LargeBinary, nullable=True)

    @hybrid_property
    def zip_file_size(self):
        size = len(self.zip_file_content)
        return get_printable_size(size)

    def __str__(self):
        return f"<SiteTemplate> {self.name}"


class SshConfig(BaseModel):
    private_key = Column(Text, nullable=True)
    public_key = Column(Text, nullable=True)

    @staticmethod
    def generate_ssh_key_pair(ssh_name: str = PROJECT_NAME) -> Tuple[str, str]:
        private_key_io = StringIO()
        public_key_io = StringIO()

        key = paramiko.RSAKey.generate(4096)
        key.write_private_key(private_key_io)
        private_key_str = private_key_io.getvalue()

        public_key_header = f"{key.get_name()} "
        public_key_body = f"{key.get_base64()} "
        public_key_footer = f"{ssh_name}@{os.uname()[1]}"
        public_key_content = [public_key_header, public_key_body, public_key_footer]
        for public_key_data in public_key_content:
            public_key_io.write(public_key_data)
        public_key_str = public_key_io.getvalue()

        return private_key_str, public_key_str

    def __str__(self):
        return f"<SshConfig> {self.public_key}"
