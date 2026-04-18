from sqlalchemy import Column, String, Integer, ForeignKey, Enum
from sqlalchemy.orm import relationship, declarative_base
from storage.entity.base_entity import BaseEntity
from constants.fail_cause import FailCause
Base = declarative_base()

class MessageDirectionFailEntity(BaseEntity):
    __tablename__ = "message_direction_fail"

    message = Column(String(255), nullable=False)
    fail_cause = Column(Enum(FailCause), nullable=False)

    message_direction_id = Column(Integer, ForeignKey("message_direction.id"))

    message_direction_entity = relationship("MessageDirectionEntity", back_populates="fail_list")

    def __init__(self, message_direction_entity, message: str = "", fail_cause: FailCause = FailCause.IMPOSSILBE):
        super().__init__()
        self.message_direction_entity = message_direction_entity
        self.message = message
        self.fail_cause = fail_cause