from dto.constraint_collect_dto import Cause
from storage.entity.base_entity import BaseEntity
from sqlalchemy import Column, String, Integer, ForeignKey, Text
from sqlalchemy.orm import relationship


class GenerateCauseEntity(BaseEntity):
    __tablename__ = 'generate_cause'

    name = Column(String(255), nullable=False)
    sentence = Column(Text, nullable=False)

    generate_rule_id = Column(Integer, ForeignKey("generate_rule.id"))
    generate_rule_entity = relationship("GenerateRuleEntity", back_populates="generate_cause_list")


    def __init__(self, generate_rule_entity, cause: Cause):
        super().__init__()
        self.generate_rule_entity = generate_rule_entity
        self.name = cause.name
        self.sentence = cause.sentence

    def to_dto(self)->Cause:
        return Cause(
            name = self.name,
            sentence=self.sentence,
        )
