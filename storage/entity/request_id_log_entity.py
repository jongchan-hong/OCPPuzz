from storage.entity.base_entity import BaseEntity
from sqlalchemy import Column, String, Boolean


class RequestIdLogEntity(BaseEntity):
    __tablename__ = 'request_id_log'
    message = Column(String(255), nullable=False)
    is_active = Column(Boolean, nullable=False, default=False)
    transaction_id = Column(String(255))