from dto.constraint_collect_dto import Constraint
from storage.entity.attribute_entity import AttributeEntity
from storage.entity.base_entity import BaseEntity, session
from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import relationship
from storage.entity.constraint_value_entry import ConstraintValueEntity
from storage.entity.operator_entity import OperatorEntity

class ConstraintEntity(BaseEntity):
    __tablename__ = 'constraint'
    from storage.entity.operator_entity import OperatorEntity
    operator_id = Column(Integer, ForeignKey("operator.id"))
    operator_entity = relationship(OperatorEntity, back_populates="constraint_list")

    attribute_id = Column(Integer, ForeignKey("attribute.id"))
    attribute_entity = relationship(AttributeEntity, back_populates="constraint_list")

    rule_id = Column(Integer, ForeignKey("gpt_rule.id"))
    rule_entity = relationship("RuleEntity", back_populates="constraint")

    value_list = relationship(
        argument= ConstraintValueEntity,
        back_populates="constraint_entity",
        cascade="all, delete-orphan"
    )

    def to_dto(self):
        return Constraint(
            attribute=self.attribute_entity.value,
            operator=self.operator_entity.value,
            values=[v.value for v in self.value_list]
        )

    def __init__(self, rule_entity, constraint: Constraint):
        super().__init__()
        self.rule_entity = rule_entity
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
                self.value_list.append(ConstraintValueEntity(
                    constraint_entity=self,
                    value=str(value),
                ))