from storage.entity.base_entity import BaseEntity
from sqlalchemy import Column, String
from sqlalchemy.orm import relationship

class OperatorEntity(BaseEntity):
    __tablename__ = 'operator'

    value = Column(String(255), unique=True)

    constraint_list = relationship(
        argument="ConstraintEntity",
        back_populates="operator_entity",
        cascade="all, delete-orphan"
    )

    condition_list = relationship(
        argument="ConditionEntity",
        back_populates="operator_entity",
        cascade="all, delete-orphan"
    )

    generate_constraint_list  = relationship(
        argument="GenerateConstraintEntity",
        back_populates="operator_entity",
        cascade="all, delete-orphan"
    )

    generate_condition_list = relationship(
        argument="GenerateConditionEntity",
        back_populates="operator_entity",
        cascade="all, delete-orphan"
    )

    def __init__(self, value:str):
        super().__init__()
        self.value = value