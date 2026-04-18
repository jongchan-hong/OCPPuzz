from storage.entity.base_entity import BaseEntity
from sqlalchemy import Column, Integer, ForeignKey, Text
from sqlalchemy.orm import relationship


class PreConfigurationVariableValueEntity(BaseEntity):
    __tablename__ = 'pre_configuration_variable_value'
    value = Column(Text, nullable=False)

    pre_configuration_variable_id = Column(Integer, ForeignKey("pre_configuration_variable.id"))
    pre_configuration_variable_entity = relationship("PreConfigurationVariableEntity", back_populates="value_list")
