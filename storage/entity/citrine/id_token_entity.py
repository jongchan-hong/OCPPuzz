
from sqlalchemy import Column, Integer, String, DateTime, create_engine
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
from sqlalchemy import ForeignKey, ARRAY
from sqlalchemy.orm import relationship

Base = declarative_base()

# entity/models.py

class IdTokenEntity(Base):
    __tablename__ = 'IdTokens'
    id = Column(Integer, primary_key=True, autoincrement=True)
    idToken = Column(String)
    type = Column(String)
    createdAt = Column(DateTime, default=datetime.utcnow)
    updatedAt = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    authorization = relationship("AuthorizationEntity", back_populates="idToken", uselist=False)


class AuthorizationEntity(Base):
    __tablename__ = 'Authorizations'
    id = Column(Integer, primary_key=True, autoincrement=True)
    allowedConnectorTypes = Column(ARRAY(String))
    disallowedEvseIdPrefixes = Column(ARRAY(String))
    idTokenId = Column(Integer, ForeignKey('IdTokens.id', onupdate='CASCADE'), unique=True)
    idTokenInfoId = Column(Integer, nullable=True)
    createdAt = Column(DateTime, default=datetime.utcnow, nullable=False)
    updatedAt = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    idToken = relationship("IdTokenEntity", back_populates="authorization")
