from typing import Union

from fastapi import APIRouter
from fastapi import Depends
from fastapi import File
from fastapi import Form
from fastapi import HTTPException
from fastapi import UploadFile
from fastapi import status
from fastapi.encoders import jsonable_encoder

from app.api.utils.db import get_db
from app.api.utils.query import C2PaginationQuery
from app.api.utils.query import DomainIspPaginationQuery
from app.api.utils.query import PaginationQuery
from app.api.utils.query import VpsIspPaginationQuery
from app.crud.crud_config import crud_c2
from app.crud.crud_config import crud_isp
from app.crud.crud_config import crud_site_template
from app.crud.crud_config import crud_ssh_config
from app.db.session import Session
from app.models.config import Isp
from app.schemas.base import BaseCrudStatusResponse
from app.schemas.base import BasePaginationQuerySchema
from app.schemas.base import TaskResponse
from app.schemas.config import C2PaginationResponse
from app.schemas.config import C2ProfileCreate
from app.schemas.config import C2ProfileCreateResponse
from app.schemas.config import C2ProfileItemResponse
from app.schemas.config import C2ProfileUpdate
from app.schemas.config import DomainIspCreate
from app.schemas.config import IspAvailableResponse
from app.schemas.config import IspItemResponse
from app.schemas.config import IspPaginationQuerySchema
from app.schemas.config import IspPaginationResponse
from app.schemas.config import IspUpdate
from app.schemas.config import SiteTemplateItem
from app.schemas.config import SiteTemplateItemResponse
from app.schemas.config import SiteTemplatePaginationResponse
from app.schemas.config import SiteTemplateUpdateSchema
from app.schemas.config import SshConfigResponse
from app.schemas.config import VpsIspCreate
from app.tasks.app import celery_app


router = APIRouter()


@router.get('/isp/available', response_model=IspAvailableResponse)
def get_available_isp():
    return dict(result=Isp.get_available_isp())


@router.get('/isp/vps/reload', response_model=TaskResponse)
def reload_vps_config():
    task = celery_app.send_task("reload_vps_isp_config")
    return dict(result=task)


@router.get("/isp/vps", response_model=IspPaginationResponse)
def get_vps_isp_profile(
    db: Session = Depends(get_db),
    *,
    query: IspPaginationQuerySchema = Depends(VpsIspPaginationQuery),
):
    query_data = IspPaginationQuerySchema.from_orm(query).dict(skip_defaults=True)
    isp_pagination_data = crud_isp.paginate(db, **query_data)

    return dict(result=isp_pagination_data)


@router.post("/isp/vps", status_code=status.HTTP_201_CREATED, response_model=IspItemResponse)
def create_vps_isp_profile(
    db: Session = Depends(get_db),
    *,
    vps_isp_profile: VpsIspCreate,
):
    vps_isp_config = crud_isp.create(db, obj_in=vps_isp_profile, serializer=None)
    return dict(result=vps_isp_config)


@router.get("/isp/domain", response_model=IspPaginationResponse)
def get_domain_isp_profile(
    db: Session = Depends(get_db),
    *,
    query: IspPaginationQuerySchema = Depends(DomainIspPaginationQuery),
):
    query_data = IspPaginationQuerySchema.from_orm(query).dict(skip_defaults=True)
    isp_pagination_data = crud_isp.paginate(db, **query_data)

    return dict(result=isp_pagination_data)


@router.post("/isp/domain", status_code=status.HTTP_201_CREATED, response_model=IspItemResponse)
def create_domain_isp_profile(
    db: Session = Depends(get_db),
    *,
    domain_isp_profile: DomainIspCreate,
):
    domain_isp_config = crud_isp.create(db, obj_in=domain_isp_profile, serializer=None)
    return dict(result=domain_isp_config)


@router.put("/isp/{isp_id:int}", response_model=IspItemResponse)
def update_isp_profile(
    db: Session = Depends(get_db),
    *,
    isp_id: int,
    isp_profile: IspUpdate,
):
    update_result = crud_isp.update(db_session=db, obj_id=isp_id, obj_in=isp_profile)
    return dict(result=update_result)


@router.delete("/isp/{isp_id:int}", response_model=BaseCrudStatusResponse)
def delete_isp_profile(
    db: Session = Depends(get_db),
    *,
    isp_id: int,
):
    # check exists of relation data
    relation_data_exists = crud_isp.check_relation_data_exists(
        db_session=db, id=isp_id, relation_key_list=['domain', 'vps']
    )
    if relation_data_exists:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="exists relation data",
        )
    delete_status = crud_isp.remove(db_session=db, id=isp_id)
    result = {
        "result": dict(status=delete_status)
    }
    return result


@router.get("/c2", response_model=C2PaginationResponse)
def get_c2_profile_list(
    db: Session = Depends(get_db),
    *,
    query: BasePaginationQuerySchema = Depends(C2PaginationQuery),
):
    query_data = BasePaginationQuerySchema.from_orm(query).dict(skip_defaults=True)
    c2_pagination_data = crud_c2.paginate(db, **query_data)
    return dict(result=c2_pagination_data)


@router.get("/c2/{profile_id}", response_model=C2ProfileItemResponse)
def get_c2_profile_detail(
    db: Session = Depends(get_db),
    *,
    profile_id: int
):
    c2_data = crud_c2.get(db, profile_id)
    return dict(result=c2_data)


@router.post(
    "/c2",
    status_code=status.HTTP_201_CREATED,
    response_model=C2ProfileCreateResponse,
    response_model_exclude={'profile_content'}
)
async def create_c2_profile(
    db: Session = Depends(get_db),
    name: str = Form(...),
    profile: UploadFile = File(...),
    remark: str = Form(None),
):
    c2_profile_obj = C2ProfileCreate(
        name=name,
        remark=remark,
        profile_name=profile.filename,
        profile_content=await profile.read()
    )
    created_data = crud_c2.create(db, obj_in=c2_profile_obj)
    return dict(result=created_data)


@router.put("/c2/{profile_id:int}", response_model=C2ProfileItemResponse)
def update_c2_profile(
    db: Session = Depends(get_db),
    *,
    profile_id: int,
    c2_profile: C2ProfileUpdate,
):
    update_result = crud_c2.update(db_session=db, obj_id=profile_id, obj_in=c2_profile)
    return dict(result=update_result)


@router.delete("/c2/{profile_id}", response_model=BaseCrudStatusResponse)
def delete_c2_profile(
    db: Session = Depends(get_db),
    *,
    profile_id: int
):
    delete_status = crud_c2.remove(db_session=db, id=profile_id)
    return {
        "result": dict(status=delete_status)
    }


@router.get("/template/site", response_model=SiteTemplatePaginationResponse)
def get_site_template_list(
    db: Session = Depends(get_db),
    *,
    query: BasePaginationQuerySchema = Depends(PaginationQuery),
):
    query_data = BasePaginationQuerySchema.from_orm(query).dict(skip_defaults=True)
    template_site_pagination_data = crud_site_template.paginate(db, **query_data)

    return dict(result=template_site_pagination_data)


@router.post(
    "/template/site",
    status_code=status.HTTP_201_CREATED,
    response_model=SiteTemplateItemResponse,
)
async def create_site_template(
    db: Session = Depends(get_db),
    name: str = Form(...),
    zip_file: UploadFile = File(..., alias='zipFile'),
    remark: Union[str, None] = Form(None),
):
    site_template_profile = dict(
        name=name,
        remark=remark,
        zip_file_name=zip_file.filename,
        zip_file_content=await zip_file.read()
    )
    created_data = crud_site_template.create_site_template(
        db, site_template_profile
    )
    return dict(result=created_data)


@router.put(
    "/template/site/{site_template_id}",
    response_model=BaseCrudStatusResponse,
)
async def update_site_template(
    db: Session = Depends(get_db),
    *,
    site_template_profile: SiteTemplateUpdateSchema
):
    update_result = crud_site_template.update_site_template(
        db_session=db,
        template_id=site_template_profile.id,
        **site_template_profile.dict(exclude={'id'})
    )
    update_status = {
        'status': bool(update_result)
    }
    return dict(result=update_status)


@router.put(
    "/template/site/{site_template_id}",
    response_model=BaseCrudStatusResponse,
)
async def upload_site_template_file(
    db: Session = Depends(get_db),
    *,
    site_template_id: int,
    zip_file: UploadFile = File(..., alias='zipFile'),
):
    update_result = crud_site_template.update_site_template(
        db_session=db,
        template_id=site_template_id,
        zip_file_name=zip_file.filename,
        zip_file_content=await zip_file.read()
    )
    return dict(result=bool(update_result))


@router.delete(
    "/template/site/{site_template_id}",
    response_model=BaseCrudStatusResponse,
)
async def delete_site_template(
    db: Session = Depends(get_db),
    *,
    site_template_id: int
):
    delete_result = {
        'status': crud_site_template.remove(db_session=db, id=site_template_id)
    }
    return dict(result=delete_result)


@router.get("/ssh", response_model=SshConfigResponse)
def get_ssh_config(db: Session = Depends(get_db)):
    ssh_config = crud_ssh_config.get_config(db)
    return dict(result=ssh_config)


@router.post("/ssh", response_model=SshConfigResponse)
def create_ssh_config(db: Session = Depends(get_db)):
    ssh_config = crud_ssh_config.get_or_create_config(db)
    return dict(result=ssh_config)
