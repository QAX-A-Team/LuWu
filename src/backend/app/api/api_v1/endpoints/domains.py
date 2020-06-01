from fastapi import APIRouter
from fastapi import Depends
from pydantic import ValidationError
from pydantic.error_wrappers import ErrorWrapper
from starlette import status

from app.api.utils.db import get_db
from app.api.utils.query import PaginationQuery
from app.crud.crud_config import crud_isp
from app.crud.crud_domain import crud_domain
from app.crud.crud_domain import crud_domain_grow
from app.crud.crud_domain import crud_domain_task
from app.db.session import Session
from app.schemas.base import BaseCrudStatusResponse
from app.schemas.base import BasePaginationQuerySchema
from app.schemas.base import BaseSuccessfulResponseModel
from app.schemas.base import TaskResponse
from app.schemas.domain import DomainCreate
from app.schemas.domain import DomainGrowCreateSchema
from app.schemas.domain import DomainGrowPaginationResponse
from app.schemas.domain import DomainMonitorPaginationResponse
from app.schemas.domain import DomainMonitorSchema
from app.schemas.domain import DomainMonitorTaskResponse
from app.schemas.domain import DomainPaginationResponse
from app.schemas.domain import PurchasableDomainQuerySchema
from app.schemas.domain import PurchasableDomainResponse
from app.schemas.domain import PurchaseDomainSchema
from app.schemas.domain import VerifyDomainSchema
from app.tasks.app import celery_app

router = APIRouter()


@router.get("/reload", response_model=TaskResponse)
def reload_domain_data():
    task = celery_app.send_task("reload_domain_dns_record")
    task.get()

    return dict(result=task)


@router.get("/", response_model=DomainPaginationResponse)
def get_domain_list(
    db: Session = Depends(get_db),
    *,
    query: BasePaginationQuerySchema = Depends(PaginationQuery),
):
    query_data = BasePaginationQuerySchema.from_orm(query).dict(skip_defaults=True)
    domain_pagination_data = crud_domain.paginate(db, **query_data)

    return dict(result=domain_pagination_data)


@router.post("/", response_model=DomainCreate)
def create_domain(
    db: Session = Depends(get_db),
    *,
    domain_config: DomainCreate
):
    if crud_domain.exists(db_session=db, domain=domain_config.domain):
        raise ValidationError(
            [ErrorWrapper(Exception('domain already exists'), loc="domain")],
            model=DomainCreate,
        )

    domain_data = crud_domain.create(db, obj_in=domain_config, serializer=None)
    celery_app.send_task("load_domain_extra_data", args=[domain_data.id])
    return dict(result=domain_data)


@router.delete("/{domain_id}", response_model=BaseCrudStatusResponse)
def delete_domain(
    db: Session = Depends(get_db),
    *,
    domain_id: int
):
    result = {
        'result': crud_domain.remove(db_session=db, id=domain_id)
    }
    return result


@router.post("/purchasable", response_model=PurchasableDomainResponse)
def get_purchasable_domain_data(
    domain_profile: PurchasableDomainQuerySchema,
):
    task = celery_app.send_task(
        "detect_domain_purchasable", kwargs=domain_profile.dict()
    )
    task_result = task.get()

    return dict(result=task_result)


@router.post("/purchase", status_code=status.HTTP_201_CREATED)
def purchase_domain(
    db: Session = Depends(get_db),
    *,
    domain_profile: PurchaseDomainSchema
):
    domain_isp = crud_isp.get(
        db_session=db,
        id=domain_profile.isp_id,
    )
    if domain_isp and domain_isp.provider_name != domain_profile.provider_name:
        raise ValidationError(
            [ErrorWrapper(Exception('provider_name is not matched'), loc="provider_name")],
            model=PurchaseDomainSchema,
        )

    purchase_task = celery_app.send_task(
        "purchase_domain", kwargs=domain_profile.dict()
    )
    purchase_result = purchase_task.get()
    return dict(result=purchase_result)


@router.post("/verify")
def verify_domain(
    domain_profile: VerifyDomainSchema
):
    task = celery_app.send_task(
        "verify_domain", kwargs=domain_profile.dict()
    )
    task_result = task.get()
    return dict(result=task_result)


@router.get("/monitor", response_model=DomainMonitorPaginationResponse)
def get_domain_monitor_task_list(
    db: Session = Depends(get_db),
    *,
    query: BasePaginationQuerySchema = Depends(PaginationQuery),
):
    query_data = BasePaginationQuerySchema.from_orm(query).dict(skip_defaults=True)
    domain_task_pagination_data = crud_domain_task.paginate(db, **query_data)

    return dict(result=domain_task_pagination_data)


@router.post("/monitor", response_model=DomainMonitorTaskResponse, status_code=status.HTTP_201_CREATED)
def create_domain_monitor_task(
    db: Session = Depends(get_db),
    *,
    monitor_profile: DomainMonitorSchema
):
    if crud_domain_task.exists(db_session=db, domain_id=monitor_profile.domain_id):
        raise ValidationError(
            [ErrorWrapper(Exception('domain is already under monitor'), loc="domain_id")],
            model=DomainMonitorSchema,
        )

    monitor_task_obj = crud_domain_task.create(db_session=db, obj_in=monitor_profile, serializer=None)
    return dict(result=monitor_task_obj)


@router.put("/monitor/{task_id}", response_model=BaseSuccessfulResponseModel)
def update_domain_monitor(
    db: Session = Depends(get_db),
    *,
    task_id: int,
    monitor_profile: DomainMonitorSchema
):
    update_result = crud_domain_task.update(db_session=db, obj_id=task_id, obj_in=monitor_profile)
    return dict(result=update_result)


@router.delete("/monitor/{task_id}", response_model=BaseCrudStatusResponse)
def delete_domain_monitor(
    db: Session = Depends(get_db),
    *,
    task_id: int
):
    delete_result = {
        'status': crud_domain_task.remove(db_session=db, id=task_id)
    }
    return dict(result=delete_result)


@router.get("/grow", response_model=DomainGrowPaginationResponse)
def get_domain_grow_task_list(
    db: Session = Depends(get_db),
    *,
    query: BasePaginationQuerySchema = Depends(PaginationQuery),
):
    query_data = BasePaginationQuerySchema.from_orm(query).dict(skip_defaults=True)
    domain_grow_pagination_data = crud_domain_grow.paginate(db, **query_data)

    return dict(result=domain_grow_pagination_data)


@router.post(
    "/grow",
    response_model=BaseSuccessfulResponseModel,
    status_code=status.HTTP_201_CREATED
)
def create_domain_grow_task(
    db: Session = Depends(get_db),
    *,
    domain_grow_profile: DomainGrowCreateSchema
):
    domain_grow_obj = crud_domain_grow.create(db_session=db, obj_in=domain_grow_profile, serializer=None)
    celery_app.send_task("grow_domain", args=[domain_grow_obj.id])
    return dict(result=domain_grow_obj)


@router.delete("/grow/{grow_task_id}", response_model=BaseCrudStatusResponse)
def delete_domain_grow_task(
    db: Session = Depends(get_db),
    *,
    grow_task_id: int
):
    celery_app.send_task("destroy_grow_domain", args=[grow_task_id])

    delete_status = crud_domain_grow.remove(db_session=db, id=grow_task_id)
    delete_result = dict(
        result={
            'status': delete_status
        }
    )
    return delete_result

