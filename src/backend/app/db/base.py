import enum
import re
from datetime import datetime
from typing import Type

from sqlalchemy import Column
from sqlalchemy import DateTime
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.declarative import declared_attr


class BaseClass:
    __table_args__ = {'keep_existing': True}

    @declared_attr
    def __tablename__(cls):
        return re.sub(r'(?<!^)(?=[A-Z])', '_', cls.__name__).lower()

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    created_on = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_on = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    remark = Column(String(500), default=None)

    @staticmethod
    def serialise_enum_data(enum_data: Type[enum.Enum]):
        return [
            {
                'code': _enum.value,
                'name': _enum.name,
            }
            for _enum in enum_data
        ]


BaseModel = declarative_base(cls=BaseClass)
