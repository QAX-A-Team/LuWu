from celery.result import allow_join_result
from fastapi import APIRouter
from fastapi import Depends
from sqlalchemy.orm import Session
from starlette import status

from api.utils.db import get_db
from api.utils.query import PaginationQuery
from crud.crud_module import crud_redirector
from crud.crud_module import crud_team_server
from models.module import RedirectorBeaconType
from models.module import RedirectorC2
from schemas.base import BaseCrudStatusResponse
from schemas.base import BasePaginationQuerySchema
from schemas.base import BaseSuccessfulResponseModel
from schemas.module import RedirectorCreateSchema
from schemas.module import RedirectorPaginationResponse
from schemas.module import TeamServerCreateSchema
from schemas.module import TeamServerItemResponse
from schemas.module import TeamServerPaginationResponse
from tasks.app import celery_app

router = APIRouter()


@router.get("/team_servers/", response_model=TeamServerPaginationResponse)
def get_team_server_list(
    db: Session = Depends(get_db),
    *,
    query: BasePaginationQuerySchema = Depends(PaginationQuery),
):
    query_data = BasePaginationQuerySchema.from_orm(query).dict()
    team_server_pagination_data = crud_team_server.paginate(db, **query_data)

    return dict(result=team_server_pagination_data)


@router.post("/team_servers/", response_model=TeamServerItemResponse, status_code=status.HTTP_201_CREATED)
def create_team_server(
    db: Session = Depends(get_db),
    *,
    team_server_profile: TeamServerCreateSchema
):
    team_server_obj = crud_team_server.create(db_session=db, obj_in=team_server_profile, serializer=None)
    celery_app.send_task("deploy_team_server", args=[team_server_obj.id])
    return dict(result=team_server_obj)


@router.delete("/team_servers/{team_server_id}", response_model=BaseCrudStatusResponse)
def destroy_team_server(
    db: Session = Depends(get_db),
    *,
    team_server_id: int
):
    # 1. destroy vps
    # 2. delete ts and vps
    team_server_obj = crud_team_server.get(db_session=db, id=team_server_id)
    destroy_task = celery_app.send_task(
        "destroy_vps", args=[team_server_obj.vps_id]
    )
    with allow_join_result():
        destroy_task.get()

    delete_result = {
        'status': crud_team_server.remove(db_session=db, id=team_server_id)
    }
    return dict(result=delete_result)


@router.get("/redirectors/", response_model=RedirectorPaginationResponse)
def get_redirector_list(
    db: Session = Depends(get_db),
    *,
    query: BasePaginationQuerySchema = Depends(PaginationQuery),
):
    query_data = BasePaginationQuerySchema.from_orm(query).dict()
    redirector_pagination_data = crud_redirector.paginate(db, **query_data)

    return dict(result=redirector_pagination_data)


@router.post("/redirectors/", response_model=BaseSuccessfulResponseModel)
def create_redirector(
    db: Session = Depends(get_db),
    *,
    redirector_profile: RedirectorCreateSchema
):
    redirector_task_data = redirector_profile.dict()
    redirector = crud_redirector.create(db_session=db, obj_in=redirector_profile, serializer=None)
    celery_app.send_task("deploy_redirector", args=[redirector.id])

    return dict(result=redirector)


@router.delete("/redirectors/{redirector_id}", response_model=BaseCrudStatusResponse)
def destroy_redirector(
    db: Session = Depends(get_db),
    *,
    redirector_id: int
):
    redirector_obj = crud_redirector.get(db_session=db, id=redirector_id)
    destroy_task = celery_app.send_task(
        "destroy_vps", args=[redirector_obj.vps_id]
    )
    with allow_join_result():
        destroy_task.get()
    
    delete_result = {
        'status': crud_redirector.remove(db_session=db, id=redirector_id)
    }
    return dict(result=delete_result)


@router.get("/beacon_types", response_model=BaseSuccessfulResponseModel)
def get_beacon_type():
    beacon_types = RedirectorC2.serialise_enum_data(RedirectorBeaconType)
    return dict(result=beacon_types)

