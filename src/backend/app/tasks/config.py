from typing import List

from pydantic import parse_obj_as

from app.crud.crud_config import crud_isp
from app.db.session import session_manager
from app.schemas.config import IspItem
from app.tasks.base import BaseTask
from utils.redis import RedisPool


class ReloadVpsIspConfigTask(BaseTask):
    name = 'reload_vps_isp_config'

    def run(self, *args, **kwargs) -> dict:
        task_result = {
            'handled_vps_isp_list': []
        }

        with session_manager() as db_session:
            vps_isp_obj_list = crud_isp.get_vps_isp_list(db_session).all()
            vps_isp_data_list = parse_obj_as(List[IspItem], vps_isp_obj_list)

            for vps_isp_data in vps_isp_data_list:
                isp_provider_name = vps_isp_data.provider_name
                if isp_provider_name in task_result['handled_vps_isp_list']:
                    continue

                reload_result = self.reload_vps_isp_config(vps_isp_data.id)
                if reload_result:
                    task_result['handled_vps_isp_list'].append(isp_provider_name)

        return self.set_result(task_result)

    def reload_vps_isp_config(self, vps_isp_id: int) -> bool:
        with session_manager() as db_session:
            rp = RedisPool()
            try:
                vps_raw_spec_data = rp.get_vps_spec_data(
                    db_session=db_session, isp_id=vps_isp_id, reload=True
                )
            except:
                vps_raw_spec_data = None

        return bool(vps_raw_spec_data)


class CreateVpsIspSshKey(BaseTask):
    name = 'create_vps_isp_ssh_key'

    def run(self, vps_isp_id: int):
        create_result = {}
        # with session_manager() as db_session:
        #     vps_isp_obj = crud_isp.get(db_session=db_session, id=vps_isp_id)

        #     if vps_isp_obj and vps_isp_obj.isp_instance.is_valid_account:
        #         ssh_key_data, ssh_key_created = crud_vps_ssh_key.get_or_create_ssh_key_data(
        #             db_session, vps_isp_id
        #         )
        #         if ssh_key_created:
        #             unix_timestamp = int(self.now_time.utcnow().timestamp())
        #             isp_ssh_key_id = vps_isp_obj.isp_instance.create_ssh_key(
        #                 name=f"{ssh_key_data['name']}-{unix_timestamp}",
        #                 public_key_content=ssh_key_data['public_key']
        #             )
        #             crud_vps_ssh_key.filter_by(
        #                 db_session=db_session,
        #                 id=ssh_key_data['id']
        #             ).update({'ssh_key_id': isp_ssh_key_id})

        #         create_result.update({
        #             'ssh_key_data': ssh_key_data,
        #             'ssh_key_created': ssh_key_created
        #         })

        return self.set_result(create_result)
