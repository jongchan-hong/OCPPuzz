from dto.constraint_collect_dto import Rule
from storage.entity.base_entity import BaseEntity
from sqlalchemy import Column, String, Integer, ForeignKey
from sqlalchemy.orm import relationship
from storage.entity.generate_cause_entity import GenerateCauseEntity
from storage.entity.generate_condition_entity import GenerateConditionEntity
from storage.entity.generate_constraint_entity import GenerateConstraintEntity


class GenerateRuleEntity(BaseEntity):
    __tablename__ = 'generate_rule'

    generate_id = Column(Integer, ForeignKey('generate.id'))
    object_name = Column(String(255))
    field_name = Column(String(255))
    generate_entity = relationship(
        argument="GenerateEntity",
        back_populates="generate_rule_list"
    )

    generate_cause_list = relationship(
        argument=GenerateCauseEntity,
        back_populates="generate_rule_entity",
        cascade="all, delete-orphan"
    )

    generate_condition_list = relationship(
        argument= GenerateConditionEntity,
        back_populates="generate_rule_entity",
        cascade="all, delete-orphan"
    )

    generate_rule_combination_value_list = relationship(
        argument="GenerateRuleCombinationValueEntity",
        back_populates="generate_rule_entity",
        cascade="all, delete-orphan"
    )

    generate_constraint = relationship(
        argument= GenerateConstraintEntity,
        back_populates="generate_rule_entity",
        uselist=False
    )


    def __init__(self, generate_entity, rule: Rule, object_name, field_name, session):
        super().__init__()
        self.generate_entity = generate_entity
        self.object_name = object_name
        self.field_name = field_name

        if rule.causes:
            for cause in rule.causes:
                generate_cause_entity = GenerateCauseEntity( generate_rule_entity = self, cause=cause)
                self.generate_cause_list.append(generate_cause_entity)

        if rule.conditions:
            for condition in rule.conditions:
                generate_condition_entity = GenerateConditionEntity(generate_rule_entity=self,condition=condition, session=session)
                self.generate_condition_list.append(generate_condition_entity)

        if rule.constraint:
            generate_constraint_entity = GenerateConstraintEntity(generate_rule_entity=self,constraint=rule.constraint, session=session)
            self.generate_constraint = generate_constraint_entity

    def to_dto(self):
        return Rule(
            causes=[cause.to_dto() for cause in self.generate_cause_list],
            conditions=[condition.to_dto() for condition in self.generate_condition_list],
            constraint=self.generate_constraint.to_dto()
        )