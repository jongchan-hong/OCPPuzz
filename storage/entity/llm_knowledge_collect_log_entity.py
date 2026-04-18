from sqlalchemy import Column, String, Integer, Float, Text, ForeignKey
from sqlalchemy.orm import relationship
from storage.entity.base_entity import BaseEntity  
import json

from llm_modules.instruction_configs.knowledge_instruction_config import KnowledgeInstructionConfig


class LLMKnowledgeCollectInstructionMessageEntity(BaseEntity):
    __tablename__ = "llm_knowledge_collect_instruction_message"
    role = Column(String(50), nullable=False)
    content = Column(Text, nullable=False)

    llm_knowledge_collect_log_id = Column(Integer, ForeignKey("llm_knowledge_collect_log.id"), nullable=False)
    llm_knowledge_collect_log_entity = relationship("LLMKnowledgeCollectLogEntity", back_populates="messages")


class LLMKnowledgeCollectLogEntity(BaseEntity):
    __tablename__ = "llm_knowledge_collect_log"
    object_name = Column(String(255), nullable=False)
    provider = Column(String(255), nullable=False)
    model = Column(String(255), nullable=False)
    timeout = Column(Integer, nullable=False)
    temperature = Column(Float, nullable=False)
    response = Column(Text, nullable=False)

    messages = relationship(
        "LLMKnowledgeCollectInstructionMessageEntity",
        back_populates="llm_knowledge_collect_log_entity",
        cascade="all, delete-orphan"
    )

    llm_knowledge_collect_id = Column(Integer, ForeignKey("llm_knowledge_collect.id"))
    llm_knowledge_collect_entity = relationship("LLMKnowledgeCollectEntity", back_populates="log_list")

    def __init__(self,
        llm_knowledge_collect_entity,
        object_name: str,
        provider: str,
        model: str,
        response: str,
        knowledge_instruction_config:KnowledgeInstructionConfig
    ):
        self.llm_knowledge_collect_entity = llm_knowledge_collect_entity
        self.object_name = object_name
        self.provider = provider
        self.model = model
        self.timeout = knowledge_instruction_config.timeout
        self.temperature = knowledge_instruction_config.temperature
        self.response = response
        self.messages = [
            LLMKnowledgeCollectInstructionMessageEntity(
                llm_knowledge_collect_log_entity=self,
                role=message.role,
                content=json.dumps(message.content) if isinstance(message.content, (list, dict)) else message.content
            ) for message in knowledge_instruction_config.messages
        ]
