from sqlalchemy.dialects.mysql import LONGTEXT

from storage.entity.base_entity import BaseEntity
from sqlalchemy import Column, String, Integer, ForeignKey
from sqlalchemy.orm import relationship

class LLMKnowledgeCollectDetailEntity(BaseEntity):
    __tablename__ = 'llm_knowledge_collect_detail'

    llm_knowledge_collect_id = Column(Integer, ForeignKey("llm_knowledge_collect.id"))
    llm_knowledge_collect_entity = relationship("LLMKnowledgeCollectEntity", back_populates="detail_list")
    provider = Column(String(255))
    model = Column(String(255))
    object_name = Column(String(255))
    response = Column(LONGTEXT, nullable=False)