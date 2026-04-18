from sqlalchemy.orm import relationship

from storage.entity.base_entity import BaseEntity
from sqlalchemy import Column, Integer, ForeignKey, Boolean

class GenerateRuleCombinationValueEntity(BaseEntity):
    __tablename__ = 'generate_rule_combination_value'

    generate_rule_combination_id = Column(Integer, ForeignKey("generate_rule_combination.id"))
    generate_rule_combination_entity = relationship("GenerateRuleCombinationEntity", back_populates="generate_rule_combination_value_entity_list")

    generate_rule_id = Column(Integer, ForeignKey("generate_rule.id"))
    generate_rule_entity = relationship("GenerateRuleEntity", back_populates="generate_rule_combination_value_list")

    is_active = Column(Boolean, nullable=False, default=True)