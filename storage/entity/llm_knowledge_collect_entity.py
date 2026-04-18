
from storage.entity.base_entity import BaseEntity
from sqlalchemy import Column, String
from sqlalchemy.orm import relationship
from storage.entity.llm_knowledge_collect_detail_entity import LLMKnowledgeCollectDetailEntity
from storage.entity.llm_knowledge_collect_fail_entity import LLMKnowledgeCollectFailEntity
from storage.entity.llm_knowledge_collect_log_entity import LLMKnowledgeCollectLogEntity
from util.hash import calculate_sha256


class LLMKnowledgeCollectEntity(BaseEntity):
    __tablename__ = 'llm_knowledge_collect'

    file_path = Column(String(255), nullable=False)
    check_sum_hash = Column(String(255), nullable=False, default="")

    detail_list = relationship(LLMKnowledgeCollectDetailEntity, back_populates="llm_knowledge_collect_entity",
                               cascade="all, delete-orphan")
    log_list = relationship(LLMKnowledgeCollectLogEntity, back_populates="llm_knowledge_collect_entity",
                            cascade="all, delete-orphan")
    fail_list = relationship(LLMKnowledgeCollectFailEntity, back_populates="llm_knowledge_collect_entity",
                             cascade="all, delete-orphan")

    def __init__(self, file_path: str):
        super().__init__()
        self.file_path = file_path
        self.check_sum_hash = calculate_sha256(file_path)