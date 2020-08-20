from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

from core import config

engine = create_engine(
    config.SQLALCHEMY_DATABASE_URI,
    max_overflow=10,
    pool_size=10,
    pool_pre_ping=True,
    pool_recycle=3600,
    pool_timeout=30,
)
db_session = scoped_session(
    sessionmaker(autocommit=False, autoflush=False, bind=engine)
)
Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@contextmanager
def session_manager(session=db_session):
    try:
        yield session
        session.commit()
    except:
        session.rollback()
        raise
    finally:
        session.close()
