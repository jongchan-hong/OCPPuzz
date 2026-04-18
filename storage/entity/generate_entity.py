from sqlalchemy.orm import relationship

from storage.entity.base_entity import BaseEntity
from sqlalchemy import Column, String

from storage.entity.generate_rule_combination_entity import GenerateRuleCombinationEntity


class GenerateEntity(BaseEntity):
    __tablename__ = 'generate'
    message_name = Column(String(100), nullable=False)
    document_path = Column(String(255), nullable=False)
    json_schema_folder_path = Column(String(255), nullable=False)

    generate_rule_list = relationship(
        argument="GenerateRuleEntity",
        back_populates="generate_entity",
        cascade="all, delete-orphan"
    )

    generate_rule_combination_list = relationship(
        argument=GenerateRuleCombinationEntity,
        back_populates="generate_entity",
        cascade="all, delete-orphan"
    )

    rule_collects = relationship("GenerateRuleCollectEntity", back_populates="generate", cascade="all, delete-orphan")


