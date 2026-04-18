from sqlalchemy.orm import relationship
from storage.entity.base_entity import BaseEntity
from sqlalchemy import Column, String, Integer, ForeignKey, DateTime
from sqlalchemy.dialects.mysql import JSON


class SendTriggerEntity(BaseEntity):
    __tablename__ = 'send_trigger'

    generate_message_id = Column(Integer, ForeignKey("generate_message.id"))
    generate_message_entity = relationship("GenerateMessageEntity", back_populates="send_trigger_entity")

    project_name = Column(String(255))
    trigger_request = Column(JSON)
    error_name = Column(String(255))
    send_at = Column(DateTime)
    trigger_request_at = Column(DateTime)

