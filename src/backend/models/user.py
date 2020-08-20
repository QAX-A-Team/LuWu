from datetime import datetime

from sqlalchemy import Boolean
from sqlalchemy import Column
from sqlalchemy import DateTime
from sqlalchemy import String

from db.base import BaseModel


class User(BaseModel):
    """
    User Model
    """
    username = Column(String(64), nullable=False)
    email = Column(String, unique=True, nullable=False)
    hashed_password = Column(String(128))
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    login_time = Column(DateTime, nullable=True, default=datetime.utcnow)

    def __str__(self):
        return f"<User {self.username}>"
