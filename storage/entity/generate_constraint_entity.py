from dto.constraint_collect_dto import Constraint
from storage.entity.attribute_entity import AttributeEntity
from storage.entity.base_entity import BaseEntity
from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import relationship

from storage.entity.generate_constraint_value_entity import GenerateConstraintValueEntity
from storage.entity.operator_entity import OperatorEntity


class GenerateConstraintEntity(BaseEntity):
    __tablename__ = 'generate_constraint'
    from storage.entity.operator_entity import OperatorEntity
    operator_id = Column(Integer, ForeignKey("operator.id"))
    operator_entity = relationship(OperatorEntity, back_populates="generate_constraint_list")

    attribute_id = Column(Integer, ForeignKey("attribute.id"))
    attribute_entity = relationship(AttributeEntity, back_populates="generate_constraint_list")

    generate_rule_id = Column(Integer, ForeignKey("generate_rule.id"))
    generate_rule_entity = relationship("GenerateRuleEntity", back_populates="generate_constraint")

    value_list = relationship(
        argument= GenerateConstraintValueEntity,
        back_populates="generate_constraint_entity",
        cascade="all, delete-orphan"
    )
    def to_dto(self):
        return Constraint(
            attribute=self.attribute_entity.value,
            operator=self.operator_entity.value,
            values=[v.value for v in self.value_list]
        )

    def __init__(self, generate_rule_entity, constraint: Constraint, session):
        super().__init__()
        self.generate_rule_entity = generate_rule_entity
        with session.no_autoflush:
            self.operator_entity = session.query(OperatorEntity).filter_by(value=constraint.operator).first()
            if self.operator_entity is None:
                self.operator_entity = OperatorEntity(value=constraint.operator)
                session.add(self.operator_entity)
                session.commit()

            self.attribute_entity = session.query(AttributeEntity).filter_by(value=constraint.attribute).first()
            if self.attribute_entity is None:
                self.attribute_entity = AttributeEntity(value=constraint.attribute)
                session.add(self.attribute_entity)
                session.commit()

        if constraint.values:
            for value in constraint.values:
                self.value_list.append(GenerateConstraintValueEntity(
                    generate_constraint_entity=self,
                    value=str(value),
                ))