from sqlalchemy import Column, String, Integer, ForeignKey
from storage.entity.base_entity import BaseEntity
from sqlalchemy.orm import relationship

class ConditionValueEntity(BaseEntity):
    __tablename__ = "condition_value"

    condition_id = Column(Integer, ForeignKey("condition.id"))

    value = Column(String(255), nullable=False)

    condition_entity = relationship("ConditionEntity", back_populates="value_list")

    def __init__(self, condition_entity, value: str):
        super().__init__()
        self.condition_entity = condition_entity
        self.value = value
