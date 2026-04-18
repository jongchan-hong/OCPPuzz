from sqlalchemy import Column, String, Integer, ForeignKey
from storage.entity.base_entity import BaseEntity
from sqlalchemy.orm import relationship

class GenerateConditionValueEntity(BaseEntity):
    __tablename__ = "generate_condition_value"

    condition_id = Column(Integer, ForeignKey("generate_condition.id"))

    value = Column(String(255), nullable=False)

    generate_condition_entity = relationship("GenerateConditionEntity", back_populates="value_list")

    def __init__(self, generate_condition_entity, value: str):
        super().__init__()
        self.generate_condition_entity = generate_condition_entity
        self.value = value
