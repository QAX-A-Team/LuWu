from typing import List

from sqlalchemy.orm import Session

from app.crud.base import CrudBase
from app.crud.crud_config import crud_isp
from app.models.vps import Vps


class CrudVps(CrudBase):
    def get_vps_list(self, db_session: Session) -> List:
        return db_session.query(self.model).all()

    @classmethod
    def get_specs(cls, db_session: Session, isp_id: int) -> dict:
        vps_isp_obj = crud_isp.get(db_session=db_session, id=isp_id)

        if vps_isp_obj and vps_isp_obj.is_vps_isp:
            region_list = vps_isp_obj.isp_instance.get_available_regions_list()
            os_list = vps_isp_obj.isp_instance.get_available_os_list()
            plan_list = vps_isp_obj.isp_instance.get_available_plans_list()
        else:
            os_list = []
            plan_list = []
            region_list = []

        vps_spec_data = {
            'region': region_list,
            'os': os_list,
            'plan': plan_list,
        }
        return vps_spec_data


crud_vps = CrudVps(Vps)
