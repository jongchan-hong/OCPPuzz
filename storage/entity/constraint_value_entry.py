from sqlalchemy import Column, String, Integer, ForeignKey
from storage.entity.base_entity import BaseEntity
from sqlalchemy.orm import relationship

class ConstraintValueEntity(BaseEntity):
    __tablename__ = "constraint_value"

    constraint_id = Column(Integer, ForeignKey("constraint.id"))
    value = Column(String(255), nullable=False)
    constraint_entity = relationship("ConstraintEntity", back_populates="value_list")

    def __init__(self, constraint_entity, value: str):
        super().__init__()

        self.constraint_entity = constraint_entity
        self.value = value