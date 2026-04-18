from dto.constraint_collect_dto import Condition
from storage.entity.attribute_entity import AttributeEntity
from storage.entity.base_entity import BaseEntity
from storage.entity.generate_condition_value_entity import GenerateConditionValueEntity
from storage.entity.operator_entity import OperatorEntity
from sqlalchemy import Column, String, Integer, ForeignKey
from sqlalchemy.orm import relationship


class GenerateConditionEntity(BaseEntity):
    __tablename__ = 'generate_condition'

    target = Column(String(255), nullable=True)
    from storage.entity.operator_entity import OperatorEntity

    operator_id = Column(Integer, ForeignKey("operator.id"))
    operator_entity = relationship(OperatorEntity, back_populates="generate_condition_list")

    attribute_id = Column(Integer, ForeignKey("attribute.id"))
    attribute_entity = relationship(AttributeEntity, back_populates="generate_condition_list")

    generate_rule_id = Column(Integer, ForeignKey("generate_rule.id"))
    generate_rule_entity = relationship("GenerateRuleEntity", back_populates="generate_condition_list")

    value_list = relationship(
        argument=GenerateConditionValueEntity,
        back_populates="generate_condition_entity",
        cascade="all, delete-orphan"
    )

    def to_dto(self)->Condition:
        return Condition(
            target=self.target,
            operator=self.operator_entity.value,
            values=[v.value for v in self.value_list],
            attribute=self.attribute_entity.value,
        )


    def __init__(self, generate_rule_entity, condition: Condition, session):
        super().__init__()
        self.generate_rule_entity = generate_rule_entity
        self.target = condition.target
        with session.no_autoflush:
            self.operator_entity = session.query(OperatorEntity).filter_by(value=condition.operator).first()
            if self.operator_entity is None:
                self.operator_entity = OperatorEntity(value=condition.operator)
                session.add(self.operator_entity)

            self.attribute_entity = session.query(AttributeEntity).filter_by(value=condition.attribute).first()
            if self.attribute_entity is None:
                self.attribute_entity = AttributeEntity(value=condition.attribute)
                session.add(self.attribute_entity)

        if condition.values:
            for value in condition.values:
                self.value_list.append(GenerateConditionValueEntity(
                    generate_condition_entity=self,
                    value=str(value),
                ))



