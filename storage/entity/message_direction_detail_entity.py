from sqlalchemy import Column, String, Integer, ForeignKey, DateTime, func
from sqlalchemy.orm import relationship
from storage.entity.base_entity import Base

class MessageDirectionDetailFrom(Base):
    __tablename__ = "message_direction_detail_from"
    id = Column(Integer, primary_key=True, autoincrement=True)
    message_direction_detail_id = Column(Integer, ForeignKey("message_direction_detail.id"))
    message_direction_detail_entity = relationship("MessageDirectionDetailEntity", back_populates="from_list")
    from_value = Column(String(255), nullable=False)

class MessageDirectionDetailTo(Base):
    __tablename__ = "message_direction_detail_to"

    id = Column(Integer, primary_key=True, autoincrement=True)
    message_direction_detail_id = Column(Integer, ForeignKey("message_direction_detail.id"))
    message_direction_detail_entity = relationship("MessageDirectionDetailEntity", back_populates="to_list")
    to_value = Column(String(255), nullable=False)

class MessageDirectionDetailEntity(Base):
    __tablename__ = "message_direction_detail"

    id = Column(Integer, primary_key=True, autoincrement=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, onupdate=func.now())

    message_direction_id = Column(Integer, ForeignKey("message_direction.id"))
    message_direction_entity = relationship("MessageDirectionEntity", back_populates="detail_list")

    action = Column(String(255), nullable=False)

    from_list = relationship(
        "MessageDirectionDetailFrom",
        back_populates="message_direction_detail_entity",
        cascade="all, delete-orphan"
    )
    to_list = relationship(
        "MessageDirectionDetailTo",
        back_populates="message_direction_detail_entity",
        cascade="all, delete-orphan"
    )

    def __init__(self, message_direction_entity, action: str, from_list=None, to_list=None):
        super().__init__()
        self.message_direction_entity = message_direction_entity
        self.action = action

        if from_list:
            for value in from_list:
                self.from_list.append(MessageDirectionDetailFrom(from_value=value, message_direction_detail_entity=self))
        if to_list:
            for value in to_list:
                self.to_list.append(MessageDirectionDetailTo(to_value=value, message_direction_detail_entity=self))