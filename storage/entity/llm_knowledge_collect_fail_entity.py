from sqlalchemy import Column, String, Integer, ForeignKey, Enum
from sqlalchemy.orm import relationship
from storage.entity.base_entity import BaseEntity
from constants.fail_cause import FailCause

class LLMKnowledgeCollectFailEntity(BaseEntity):
    __tablename__ = "llm_knowledge_collect_fail"
    object_name = Column(String(255), nullable=False)
    fail_cause = Column(Enum(FailCause), nullable=False)
    provider = Column(String(255), nullable=False)
    model = Column(String(255), nullable=False)
    llm_knowledge_collect_id = Column(Integer, ForeignKey("llm_knowledge_collect.id"))
    llm_knowledge_collect_entity = relationship("LLMKnowledgeCollectEntity", back_populates="fail_list")