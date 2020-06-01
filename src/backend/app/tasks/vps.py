from app.crud.crud_config import crud_isp
from app.crud.crud_config import crud_ssh_config
from app.crud.crud_vps import crud_vps
from app.db.session import session_manager
from app.models.vps import VpsStatus
from app.schemas.vps import VpsCreateSchema
from app.tasks.base import BaseTask


class CreateVpsTask(BaseTask):
    """
    Create VPS task
    """
    name = 'create_vps'

    def run(self, vps_profile: VpsCreateSchema, vps_id: int, *args, **kwargs) -> dict:
        with session_manager() as db_session:
            vps_isp_obj = crud_isp.get(db_session=db_session, id=vps_profile['isp_id'])
            ssh_key_obj = crud_ssh_config.get_config(db_session)
            extra_server_data = vps_isp_obj.isp_instance.create_server(vps_profile, ssh_key_obj.public_key)
            vps_data = dict(
                status=VpsStatus.running,
                **extra_server_data
            )
            crud_vps.update(db_session=db_session, obj_id=vps_id, obj_in=vps_data)
        return self.set_result()

    def on_failure(self, exc, task_id, args, kwargs, einfo) -> None:
        vps_id = args[-1] if isinstance(args[-1], int) else None
        if not vps_id:
            return self.log_exception(exc)

        with session_manager() as db_session:
            error_data = dict(
                status=VpsStatus.error,
                status_msg=str(einfo)
            )
            crud_vps.update(db_session=db_session, obj_id=vps_id, obj_in=error_data)


class DestroyVpsTask(BaseTask):
    """
    Destroy Vps Task
    """
    name = 'destroy_vps'

    def run(self, vps_id: int, *args, **kwargs):
        task_result = {}
        with session_manager() as db_session:
            vps_obj = crud_vps.get(db_session=db_session, id=vps_id)

            if vps_obj and vps_obj.server_id:
                task_result = vps_obj.isp.isp_instance.destroy_server(vps_obj.server_id)

        return task_result
