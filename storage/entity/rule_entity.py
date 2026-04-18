from dto.constraint_collect_dto import Rule
from storage.entity.base_entity import BaseEntity, session
from sqlalchemy import Column, Integer, ForeignKey, Boolean
from sqlalchemy.orm import relationship

from storage.entity.cause_entity import CauseEntity
from storage.entity.condition_entity import ConditionEntity
from storage.entity.constraint_entity import ConstraintEntity


class RuleEntity(BaseEntity):
    __tablename__ = 'gpt_rule'

    rule_collect_detail_id = Column(Integer, ForeignKey('rule_collect_detail.id'))
    rule_collect_detail_entity = relationship(
        argument="RuleCollectDetailEntity",
        back_populates="rule_list"
    )
    cause_list = relationship(
        argument=CauseEntity,
        back_populates="rule_entity",
        cascade="all, delete-orphan"
    )

    condition_list = relationship(
        argument= ConditionEntity,
        back_populates="rule_entity",
        cascade="all, delete-orphan"
    )

    constraint = relationship(
        argument= ConstraintEntity,
        back_populates="rule_entity",
        uselist=False
    )

    is_active = Column(Boolean, nullable=False, default=True)
    is_valid = Column(Boolean, nullable=False, default=True)


    def __init__(self, rule_collect_detail_entity, rule: Rule):
        super().__init__()
        self.rule_collect_detail_entity = rule_collect_detail_entity

        if rule.causes:
            for cause in rule.causes:
                cause_entity = CauseEntity( rule_entity = self, cause=cause)
                session.add(cause_entity)
                self.cause_list.append(cause_entity)

        if rule.conditions:
            for condition in rule.conditions:
                condition_entity = ConditionEntity(rule_entity=self,condition=condition)
                session.add(condition_entity)
                self.condition_list.append(condition_entity)

        if rule.constraint:
            constraint_entity = ConstraintEntity(rule_entity=self,constraint=rule.constraint)
            session.add(constraint_entity)
            self.constraint = constraint_entity

    def to_dto(self):
        return Rule(
            causes=[cause.to_dto() for cause in self.cause_list],
            conditions=[condition.to_dto() for condition in self.condition_list],
            constraint=self.constraint.to_dto()
        )