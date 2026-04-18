from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import relationship
from storage.entity.base_entity import BaseEntity

class GenerateRuleCollectEntity(BaseEntity):
    __tablename__ = 'generate_rule_collect'

    generate_id = Column(Integer, ForeignKey('generate.id'), primary_key=True)
    rule_collect_id = Column(Integer, ForeignKey('rule_collect.id'), primary_key=True)

    generate = relationship("GenerateEntity", back_populates="rule_collects")
    rule_collect = relationship("RuleCollectEntity", back_populates="generates")