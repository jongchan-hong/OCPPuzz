from sqlalchemy import Column, Integer, DateTime, func
from sqlalchemy.ext.declarative import declarative_base
from storage.db_engine import engine
from sqlalchemy.orm import sessionmaker, scoped_session
from contextlib import contextmanager


SessionLocal = sessionmaker(bind=engine)
session = SessionLocal()
Base = declarative_base()

SessionFactory = sessionmaker(bind=engine, expire_on_commit=False)
ScopedSession = scoped_session(SessionFactory)

@contextmanager
def get_session():
    session = ScopedSession()
    try:
        yield session
        session.commit()
    except:
        session.rollback()
        raise
    finally:
        session.close()

class BaseEntity(Base):
    __abstract__ = True

    id = Column(Integer, primary_key=True, autoincrement=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, onupdate=func.now())

