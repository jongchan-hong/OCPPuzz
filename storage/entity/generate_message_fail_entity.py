from sqlalchemy.orm import relationship
from storage.entity.base_entity import BaseEntity
from sqlalchemy import Column, String, Integer, ForeignKey, Text


class GenerateMessageFailEntity(BaseEntity):
    __tablename__ = 'generate_message_fail'

    exception = Column(String(100), nullable=False)
    cause = Column(Text, nullable=False)

    generate_rule_combination_id = Column(Integer, ForeignKey('generate_rule_combination.id'))
    generate_rule_combination_entity = relationship("GenerateRuleCombinationEntity", back_populates="generate_message_fail_list")

    test_id = Column(Integer, ForeignKey("test.id"))
    test_entity = relationship("TestEntity", back_populates="generate_message_fail_list")