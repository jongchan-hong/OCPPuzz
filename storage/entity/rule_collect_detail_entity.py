from dto.constraint_collect_dto import ConstraintCollectDTO
from storage.entity.base_entity import BaseEntity, session
from sqlalchemy import Column, String, Integer, ForeignKey
from sqlalchemy.orm import relationship

from storage.entity.rule_entity import RuleEntity


class RuleCollectDetailEntity(BaseEntity):
    __tablename__ = 'rule_collect_detail'

    rule_collect_id = Column(Integer, ForeignKey("rule_collect.id"))
    rule_collect_entity = relationship("RuleCollectEntity", back_populates="detail_list")
    object_name = Column(String(255))
    name = Column(String(255))
    rule_list = relationship(
        argument=RuleEntity,
        back_populates="rule_collect_detail_entity",
        cascade="all, delete-orphan"
    )
    def get_active_rule_list(self):
        return [rule for rule in self.rule_list if rule.is_active == True]

    def get_valid_rule_list(self):
        return [rule for rule in self.rule_list if rule.is_valid == True]

    def __init__(self, rule_collect_entity, object_name:str, constraint_collect_dto: ConstraintCollectDTO):
        super().__init__()
        self.rule_collect_entity = rule_collect_entity
        self.object_name = object_name
        self.name = constraint_collect_dto.name
        if constraint_collect_dto.rules:
            for rule in constraint_collect_dto.rules:
                rule_entity = RuleEntity(rule_collect_detail_entity = self,rule = rule)
                session.add(rule_entity)
                self.rule_list.append(rule_entity)



