from typing import Optional

from sqlalchemy.orm import Query
from sqlalchemy.orm import Session

from crud.base import CreateSchemaType
from crud.base import CrudBase
from crud.base import ModelType
from crud.base import UpdateSchemaType
from models.config import C2Profile
from models.config import Isp
from models.config import IspApiKey
from models.config import IspType
from models.config import SiteTemplate
from models.config import SshConfig


class CrudConfig(CrudBase):
    ...


class CrudIsp(CrudConfig):
    def get_available_api_token(
        self, db_session: Session, isp_type=IspType.domain, isp_provider=None
    ) -> Isp:
        isp_obj = (
            db_session.query(self.model)
            .filter_by(type=isp_type, provider=isp_provider)
            .first()
        )
        api_key = isp_obj.api_key if isp_obj else None
        return api_key

    def get_domain_isp_list(self, db_session: Session, isp_provider=None) -> Query:
        return self.get_specific_isp_list(
            db_session=db_session, isp_type=IspType.domain, isp_provider=isp_provider
        )

    def get_vps_isp_list(self, db_session: Session, isp_provider=None) -> Query:
        vps_isp_list = self.get_specific_isp_list(
            db_session=db_session, isp_type=IspType.vps, isp_provider=isp_provider
        )
        return vps_isp_list

    def get_vps_isp_ssh_key(self, db_session: Session):
        return self.filter_by(db_session=db_session)

    def get_specific_isp_list(
        self, db_session: Session, *, isp_type: IspType, isp_provider=None
    ) -> Query:
        query_condition = {"type": isp_type}
        if isp_provider:
            query_condition["provider"] = isp_provider
        return self.filter_by(db_session, **query_condition)

    def update(
        self, db_session: Session, *, obj_id: int, obj_in: UpdateSchemaType
    ) -> ModelType:
        db_obj = self.get(db_session, obj_id)
        super().update(db_session=db_session, obj_id=obj_id, obj_in=obj_in)
        crud_api_key.update(
            db_session=db_session, obj_id=db_obj.isp_api_key.id, obj_in=obj_in
        )

        update_datetime = max([db_obj.isp_api_key.updated_on, db_obj.updated_on])
        db_obj.isp_api_key.updated_on = update_datetime
        db_obj.updated_on = update_datetime
        db_session.commit()

        return db_obj


class CrudCommandAndControl(CrudConfig):
    def create(self, db_session: Session, *, obj_in: CreateSchemaType) -> ModelType:
        db_obj = self.model(**obj_in.dict(skip_defaults=True))
        db_session.add(db_obj)
        db_session.commit()
        db_session.refresh(db_obj)
        return db_obj


class CrudSiteTemplate(CrudConfig):
    def create_site_template(
        self, db_session: Session, site_template_data: dict
    ) -> ModelType:
        db_obj = self.model(**site_template_data)
        db_session.add(db_obj)
        db_session.commit()
        db_session.refresh(db_obj)
        return db_obj

    def update_site_template(
        self, db_session: Session, template_id: int, **site_template_data
    ) -> ModelType:
        db_obj = self.get(db_session=db_session, id=template_id)
        for site_template_key in site_template_data:
            setattr(db_obj, site_template_key, site_template_data[site_template_key])
        db_session.add(db_obj)
        db_session.commit()
        db_session.refresh(db_obj)
        return db_obj


class CrudSshConfig(CrudConfig):
    def get_config(self, db_session: Session) -> Optional[ModelType]:
        return db_session.query(self.model).one_or_none()

    def create_config(self, db_session: Session) -> ModelType:
        private_key, public_key = self.model.generate_ssh_key_pair()
        ssh_config_obj = dict(private_key=private_key, public_key=public_key)

        return self.create(db_session=db_session, obj_in=ssh_config_obj)

    def get_or_create_config(self, db_session: Session) -> ModelType:
        ssh_config = self.get_config(db_session)

        if not ssh_config:
            ssh_config = self.create_config(db_session)
        return ssh_config


crud_isp = CrudIsp(Isp)
crud_api_key = CrudConfig(IspApiKey)
crud_c2 = CrudCommandAndControl(C2Profile)
crud_site_template = CrudSiteTemplate(SiteTemplate)
crud_ssh_config = CrudSshConfig(SshConfig)
