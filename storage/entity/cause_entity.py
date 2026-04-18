from dto.constraint_collect_dto import Cause
from storage.entity.base_entity import BaseEntity
from sqlalchemy import Column, String, Integer, ForeignKey, Text
from sqlalchemy.orm import relationship


class CauseEntity(BaseEntity):
    __tablename__ = 'cause'

    name = Column(String(255), nullable=False)
    sentence = Column(Text, nullable=False)

    rule_id = Column(Integer, ForeignKey("gpt_rule.id"))
    rule_entity = relationship("RuleEntity", back_populates="cause_list")


    def __init__(self, rule_entity, cause: Cause):
        super().__init__()
        self.rule_entity = rule_entity
        self.name = cause.name
        self.sentence = cause.sentence

    def to_dto(self)->Cause:
        return Cause(
            name = self.name,
            sentence=self.sentence,
        )