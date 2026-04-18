from sqlalchemy import Column, Integer, DateTime, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class EvseEntity(Base):
    __tablename__ = 'Evses'

    databaseId = Column(Integer, primary_key=True, autoincrement=True)
    id = Column(Integer)
    connectorId = Column(Integer)
    createdAt = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updatedAt = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint('id', 'connectorId'),
    )