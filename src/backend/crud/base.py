from math import ceil
from typing import Callable
from typing import Generic
from typing import List
from typing import Optional
from typing import Type
from typing import TypeVar

from fastapi.encoders import jsonable_encoder
from pydantic import parse_obj_as
from sqlalchemy import desc
from sqlalchemy import inspect
from sqlalchemy.orm import Session

from db.base import BaseModel
from schemas.base import BaseSchema

ModelType = TypeVar("ModelType", bound=BaseModel)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class Pagination(object):
    """Internal helper class returned by :meth:`BaseQuery.paginate`.  You
    can also construct it from any other SQLAlchemy query object if you are
    working with other libraries.  Additionally it is possible to pass `None`
    as query object in which case the :meth:`prev` and :meth:`next` will
    no longer work.
    """

    def __init__(self, query, page, per_page, total, items):
        #: the unlimited query object that was used to create this
        #: pagination object.
        self.query = query
        #: the current page number (1 indexed)
        self.page = int(page) or 1
        #: the number of items to be displayed on a page.
        self.per_page = int(per_page)
        #: the total number of items matching the query
        self.total = total
        #: the items for the current page
        self.items = items

    @property
    def pages(self):
        """The total number of pages"""
        if self.per_page == 0 or self.total is None:
            pages = 0
        else:
            pages = int(ceil(self.total / float(self.per_page)))
        return pages

    def prev(self, error_out=False):
        """Returns a :class:`Pagination` object for the previous page."""
        assert self.query is not None, (
            "a query object is required " "for this method to work"
        )
        return self.query.paginate(self.page - 1, self.per_page, error_out)

    @property
    def prev_num(self):
        """Number of the previous page."""
        if not self.has_prev:
            return None
        return self.page - 1

    @property
    def has_prev(self):
        """True if a previous page exists"""
        return self.page > 1

    def next(self, error_out=False):
        """Returns a :class:`Pagination` object for the next page."""
        assert self.query is not None, (
            "a query object is required " "for this method to work"
        )
        return self.query.paginate(self.page + 1, self.per_page, error_out)

    @property
    def has_next(self):
        """True if a next page exists."""
        return self.page < self.pages

    @property
    def next_num(self):
        """Number of the next page"""
        if not self.has_next:
            return None
        return self.page + 1

    def to_dict(self):
        return {
            "page": self.page,
            "prev_num": self.prev_num,
            "has_prev": self.has_prev,
            "has_next": self.has_next,
            "next_num": self.next_num,
            "total": self.total,
            "items": self.items,
        }


class CrudBase(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    def __init__(
        self,
        model: Type[ModelType],
        create_schema: CreateSchemaType = None,
        update_schema: UpdateSchemaType = None,
    ):
        """
        CRUD object with default methods to Create, Read, Update, Delete (CRUD).

        **Parameters**

        * `model`: A SQLAlchemy model class
        * `schema`: A Pydantic model (schema) class
        """
        self.model = model
        self.createSchema = create_schema
        self.updateSchema = update_schema

    def filter_by(self, db_session: Session, **filter_kwargs):
        return db_session.query(self.model).filter_by(**filter_kwargs)

    def exists(self, db_session: Session, **filter_kwargs):
        filter_query = self.filter_by(db_session=db_session, **filter_kwargs)
        return db_session.query(filter_query.exists()).scalar()

    def get(self, db_session: Session, id: int) -> Optional[ModelType]:
        return db_session.query(self.model).filter(self.model.id == id).first()

    def get_multi(self, db_session: Session, *, skip=0, limit=100) -> List[ModelType]:
        return db_session.query(self.model).offset(skip).limit(limit).all()

    def create(
        self, db_session: Session, *, obj_in: CreateSchemaType, serializer: Callable = None
    ) -> ModelType:
        if serializer:
            obj_in_data = serializer(obj_in)
        else:
            obj_in_data = obj_in.dict() if hasattr(obj_in, 'dict') else obj_in

        db_obj = self.model(**obj_in_data)
        db_session.add(db_obj)
        db_session.commit()
        db_session.refresh(db_obj)
        return db_obj

    def update(
        self, db_session: Session, *, obj_id: int, obj_in: UpdateSchemaType
    ) -> ModelType:
        db_obj = self.get(db_session, obj_id)
        if getattr(obj_in, "dict", None):
            update_data = obj_in.dict(
                skip_defaults=True,
                exclude_unset=True,
                exclude={"updated_on", "created_on", "id"},
            )
        else:
            update_data = obj_in

        for field in update_data:
            if hasattr(db_obj, field):
                setattr(db_obj, field, update_data[field])

        db_session.commit()
        db_session.refresh(db_obj)
        return db_obj

    def remove(self, db_session: Session, *, id: int) -> bool:
        result = db_session.query(self.model).filter_by(id=id).delete()
        db_session.commit()
        return result

    def paginate(
        self,
        db_session: Session,
        query=None,
        page=None,
        per_page=None,
        count=True,
        query_all=False,
        **kwargs
    ):
        if not query:
            query = (
                db_session.query(self.model)
                .filter_by(**kwargs)
                .order_by(desc(self.model.id))
            )

        if query_all:
            items = query.all()
        else:
            items = query.limit(per_page).offset((page - 1) * per_page).all()

        if not count:
            total = None
        else:
            total = query.order_by(None).count()

        return Pagination(query, page, per_page, total, items)

    def check_relation_data_exists(
        self, db_session: Session, id: int, relation_key_list: List = None
    ) -> bool:
        if not relation_key_list:
            relation_key_list = [
                model_relation.key
                for model_relation in inspect(self.model).mapper.relationships
            ]

        obj = self.get(db_session, id)
        relation_exists = (
            any(
                [
                    getattr(obj, model_relation_key, False)
                    for model_relation_key in relation_key_list
                ]
            )
            if obj
            else False
        )
        return relation_exists

    @staticmethod
    def serialize_list_obj(
        serialize_schema: Type[BaseSchema], obj_list: List[ModelType]
    ) -> List[Type[BaseModel]]:
        item_list = [
            jsonable_encoder(item)
            for item in parse_obj_as(List[serialize_schema], obj_list)
        ]
        return item_list
