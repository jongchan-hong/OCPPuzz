from sqlalchemy import Column, String
from sqlalchemy.orm import relationship

from storage.entity.base_entity import BaseEntity
from storage.entity.variable_value_entity import VariableValueEntity


class VariableEntity(BaseEntity):
    __tablename__ = 'variable'
    component_name = Column(String(255), nullable=True)
    variable_name = Column(String(255), nullable=True)
    project_name = Column(String(255), nullable=True)
    cs_name = Column(String(255), nullable=True)

    value_list = relationship(
        argument=VariableValueEntity,
        back_populates="variable_entity",
        cascade="all, delete-orphan"
    )

    def get_rule_value(self):
        return f"variable.{self.component_name}.{self.variable_name}"


    def __init__(self, component_name:String, variable_name:String, values, project_name, cs_name):
        super().__init__()
        self.component_name = component_name
        self.variable_name = variable_name
        self.project_name = project_name
        self.cs_name = cs_name
        if values:
            for value in values:
                self.value_list.append(VariableValueEntity(
                    variable_entity=self,
                    value=str(value),
                ))
