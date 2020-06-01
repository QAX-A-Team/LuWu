from celery.result import allow_join_result
from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from fastapi import Query
from pydantic import ValidationError
from pydantic.error_wrappers import ErrorWrapper
from starlette import status

from app.api.utils.db import get_db
from app.api.utils.query import PaginationQuery
from app.crud.crud_config import crud_isp
from app.crud.crud_vps import crud_vps
from app.db.session import Session
from app.schemas.base import BaseCrudStatusResponse
from app.schemas.base import BasePaginationQuerySchema
from app.schemas.base import TaskResponse
from app.schemas.vps import VpsCreateSchema
from app.schemas.vps import VpsPaginationResponse
from app.schemas.vps import VpsSpecResponse
from app.schemas.vps import VpsSpecSchema
from app.schemas.vps import VpsSshKeyResponseSchema
from app.tasks.app import celery_app
from utils.redis import RedisPool

router = APIRouter()


@router.get("/", response_model=VpsPaginationResponse)
def get_server_list(
    db: Session = Depends(get_db),
    *,
    query: BasePaginationQuerySchema = Depends(PaginationQuery),
):
    query_data = BasePaginationQuerySchema.from_orm(query).dict()
    isp_pagination_data = crud_vps.paginate(db, **query_data)
    result = dict(result=isp_pagination_data)
    return result


@router.post("/", response_model=TaskResponse)
def create_vps_server(db: Session = Depends(get_db), *, vps_profile: VpsCreateSchema):
    # validate
    vps_isp_obj = crud_isp.get(db_session=db, id=vps_profile.isp_id)
    if not vps_isp_obj:
        raise ValidationError(
            [ErrorWrapper(Exception('provider_name is not matched'), loc="isp_id")],
            model=VpsCreateSchema,
        )

    # create base vps data
    rp = RedisPool()
    vps_spec_data = rp.get_vps_spec_value(
        db_session=db,
        isp_id=vps_profile.isp_id,
        os_code=vps_profile.os_code,
        plan_code=vps_profile.plan_code,
        region_code=vps_profile.region_code
    )
    vps_config = dict(
        hostname=vps_profile.hostname,
        isp_id=vps_profile.isp_id,
        ssh_keys=vps_profile.ssh_keys,
        remark=vps_profile.remark,
        status=vps_profile.status,
        **vps_spec_data
    )

    vps_obj = crud_vps.create(db_session=db, obj_in=vps_config, serializer=None)
    task = celery_app.send_task(
        "create_vps", args=[vps_profile.dict(), vps_obj.id]
    )
    return dict(result=task)


@router.get("/{server_id:int}/reboot")
def reboot_server(
    db: Session = Depends(get_db),
    *,
    server_id: int
):
    server_obj = crud_vps.get(db_session=db, id=server_id)
    action_result = server_obj.isp.isp_instance.reboot_server(server_obj.server_id)
    return action_result


@router.get("/{server_id:int}/shutdown")
def shutdown_server(
    db: Session = Depends(get_db),
    *,
    server_id: int
):
    server_obj = crud_vps.get(db_session=db, id=server_id)
    action_result = server_obj.isp.isp_instance.shutdown_server(server_obj.server_id)
    return action_result


@router.get("/{server_id:int}/start")
def start_server(
    db: Session = Depends(get_db),
    *,
    server_id: int
):
    server_obj = crud_vps.get(db_session=db, id=server_id)
    action_result = server_obj.isp.isp_instance.start_server(server_obj.server_id)
    return action_result


@router.get("/{server_id:int}/reinstall")
def reinstall_server(
    db: Session = Depends(get_db),
    *,
    server_id: int
):
    server_obj = crud_vps.get(db_session=db, id=server_id)
    action_result = server_obj.isp.isp_instance.reinstall_server(
        server_obj.server_id, hostname=server_obj.hostname
    )
    return action_result


@router.delete("/{vps_id}", response_model=BaseCrudStatusResponse)
def destroy_vps_server(db: Session = Depends(get_db), *, vps_id: int):
    # check exists of relation data
    relation_data_exists = crud_vps.check_relation_data_exists(
        db_session=db,
        id=vps_id,
        relation_key_list=['team_servers', 'redirector_c2s', 'smtp_servers']
    )
    if relation_data_exists:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="exists relation data",
        )

    destroy_task = celery_app.send_task(
        "destroy_vps", args=[vps_id]
    )
    with allow_join_result():
        destroy_task.get()

    destroy_result = {
        'status': crud_vps.remove(db_session=db, id=vps_id)
    }

    return dict(result=destroy_result)


@router.get("/specs", response_model=VpsSpecResponse)
def get_vps_specs(db: Session = Depends(get_db), *, isp_id: int = Query(0, alias='ispId')):
    rp = RedisPool()
    vps_raw_spec_data = rp.get_vps_spec_data(db_session=db, isp_id=isp_id)
    vps_spec_data = VpsSpecSchema(**vps_raw_spec_data)

    return dict(result=vps_spec_data)


@router.get("/isp/{isp_id}/ssh_keys", response_model=VpsSshKeyResponseSchema)
def get_vps_ssh_keys(db: Session = Depends(get_db), *, isp_id: int = Query(..., alias='ispId')):
    ssh_key_list = []
    vps_isp_obj = crud_isp.get(db_session=db, id=isp_id)
    if vps_isp_obj:
        ssh_key_list = vps_isp_obj.isp_instance.get_ssh_key_list(isp_id)

    return dict(result=ssh_key_list)
