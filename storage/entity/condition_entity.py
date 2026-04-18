from dto.constraint_collect_dto import Condition
from storage.entity.attribute_entity import AttributeEntity
from storage.entity.base_entity import BaseEntity, session
from sqlalchemy import Column, String, Integer, ForeignKey
from sqlalchemy.orm import relationship

from storage.entity.condition_value_entity import ConditionValueEntity
from storage.entity.operator_entity import OperatorEntity


class ConditionEntity(BaseEntity):
    __tablename__ = 'condition'

    target = Column(String(255), nullable=True)

    from storage.entity.operator_entity import OperatorEntity

    operator_id = Column(Integer, ForeignKey("operator.id"))
    operator_entity = relationship(OperatorEntity, back_populates="condition_list")

    attribute_id = Column(Integer, ForeignKey("attribute.id"))
    attribute_entity = relationship(AttributeEntity, back_populates="condition_list")

    rule_id = Column(Integer, ForeignKey("gpt_rule.id"))
    rule_entity = relationship("RuleEntity", back_populates="condition_list")

    value_list = relationship(
        argument=ConditionValueEntity,
        back_populates="condition_entity",
        cascade="all, delete-orphan"
    )
    def to_dto(self)->Condition:
        return Condition(
            target=self.target,
            operator=self.operator_entity.value,
            values=[v.value for v in self.value_list],
            attribute=self.attribute_entity.value,
        )


    def __init__(self, rule_entity, condition: Condition):
        super().__init__()
        self.rule_entity = rule_entity
        self.target = condition.target
        with session.no_autoflush:
            self.operator_entity = session.query(OperatorEntity).filter_by(value=condition.operator).first()
            if self.operator_entity is None:
                self.operator_entity = OperatorEntity(value=condition.operator)
                session.add(self.operator_entity)
                session.commit()

            self.attribute_entity = session.query(AttributeEntity).filter_by(value=condition.attribute).first()
            if self.attribute_entity is None:
                self.attribute_entity = AttributeEntity(value=condition.attribute)
                session.add(self.attribute_entity)
                session.commit()

        if condition.values:
            for value in condition.values:
                self.value_list.append(ConditionValueEntity(
                    condition_entity=self,
                    value=str(value),
                ))



