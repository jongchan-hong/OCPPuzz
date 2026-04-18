from sqlalchemy import Column, String, Integer, Float, Text, ForeignKey
from sqlalchemy.orm import relationship
from storage.entity.base_entity import BaseEntity

class InstructionMessageEntity(BaseEntity):
    __tablename__ = "gpt_message_direction_instruction_message"
    role = Column(String(50), nullable=False)
    content = Column(Text, nullable=False)
    gpt_log_id = Column(Integer, ForeignKey("gpt_message_direction_log.id"), nullable=False)
    gpt_log_entity = relationship("GPTMessageDirectionLogEntity", back_populates="messages")

class GPTMessageDirectionLogEntity(BaseEntity):
    __tablename__ = "gpt_message_direction_log"
    message = Column(String(255), nullable=False)
    model = Column(String(255), nullable=False)
    timeout = Column(Integer, nullable=False)
    temperature = Column(Float, nullable=False)
    response = Column(Text, nullable=False)

    messages = relationship(
        "InstructionMessageEntity",
        back_populates="gpt_log_entity",
        cascade="all, delete-orphan"
    )

    message_direction_id = Column(Integer, ForeignKey("message_direction.id"))
    message_direction_entity = relationship("MessageDirectionEntity", back_populates="log_list")

    def __init__(self,
        message_direction_entity,
        message: str,
        model: str,
        timeout: int,
        temperature: float,
        response: str,
        messages: list
    ):
        self.message_direction_entity = message_direction_entity
        self.message = message
        self.model = model
        self.timeout = timeout
        self.temperature = temperature
        self.response = response
        self.messages = [
            InstructionMessageEntity(
                gpt_log_entity=self,
                role=message.role,
                content=message.content
            ) for message in messages
        ]
