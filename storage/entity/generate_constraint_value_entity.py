from sqlalchemy import Column, String, Integer, ForeignKey
from storage.entity.base_entity import BaseEntity
from sqlalchemy.orm import relationship

class GenerateConstraintValueEntity(BaseEntity):
    __tablename__ = "generate_constraint_value"

    generate_constraint_id = Column(Integer, ForeignKey("generate_constraint.id"))

    value = Column(String(255), nullable=False)

    generate_constraint_entity = relationship("GenerateConstraintEntity", back_populates="value_list")

    def __init__(self, generate_constraint_entity, value: str):
        super().__init__()

        self.generate_constraint_entity = generate_constraint_entity
        self.value = value