from storage.entity.base_entity import BaseEntity
from sqlalchemy import Column
from sqlalchemy.dialects.mysql import JSON

class CsmsTriggerLogEntity(BaseEntity):
    __tablename__ = 'csms_trigger_log'
    request = Column(JSON)
    response = Column(JSON)