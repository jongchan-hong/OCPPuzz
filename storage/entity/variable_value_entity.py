from sqlalchemy import Column, String, Integer, ForeignKey
from storage.entity.base_entity import BaseEntity
from sqlalchemy.orm import relationship

class VariableValueEntity(BaseEntity):
    __tablename__ = "variable_value"

    variable_id = Column(Integer, ForeignKey("variable.id"))

    value = Column(String(1000), nullable=False)

    variable_entity = relationship("VariableEntity", back_populates="value_list")

    def __init__(self, variable_entity, value: str):
        super().__init__()
        self.variable_entity = variable_entity
        self.value = value
