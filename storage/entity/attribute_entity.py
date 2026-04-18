from storage.entity.base_entity import BaseEntity
from sqlalchemy import Column, String
from sqlalchemy.orm import relationship

class AttributeEntity(BaseEntity):
    __tablename__ = 'attribute'

    value = Column(String(255), unique=True)

    constraint_list = relationship(
        argument="ConstraintEntity",
        back_populates="attribute_entity",
        cascade="all, delete-orphan"
    )

    condition_list = relationship(
        argument="ConditionEntity",
        back_populates="attribute_entity",
        cascade="all, delete-orphan"
    )

    generate_constraint_list = relationship(
        argument="GenerateConstraintEntity",
        back_populates="attribute_entity",
        cascade="all, delete-orphan"
    )

    generate_condition_list = relationship(
        argument="GenerateConditionEntity",
        back_populates="attribute_entity",
        cascade="all, delete-orphan"
    )
    def __init__(self, value:str):
        self.value = value
