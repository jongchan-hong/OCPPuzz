from dto.scenario_collect_dto import ConfigurationVariableDTO
from storage.entity.base_entity import BaseEntity, session
from sqlalchemy import Column, String, Integer, ForeignKey
from sqlalchemy.orm import relationship

from storage.entity.pre_configuration_variable_value_entity import PreConfigurationVariableValueEntity


class PreConfigurationVariableEntity(BaseEntity):
    __tablename__ = 'pre_configuration_variable'

    scenario_collect_detail_id = Column(Integer, ForeignKey('scenario_collect_detail.id'))
    scenario_collect_detail_entity = relationship(
        argument="ScenarioCollectDetailEntity",
        back_populates="pre_configuration_variable_list"
    )

    name = Column(String(100))

    value_list = relationship(
        argument=PreConfigurationVariableValueEntity,
        back_populates="pre_configuration_variable_entity",
        cascade="all, delete-orphan"
    )


    def __init__(self, scenario_collect_detail_entity, pre_configuration_variable_dto: ConfigurationVariableDTO):
        super().__init__()
        self.scenario_collect_detail_entity = scenario_collect_detail_entity
        self.name = pre_configuration_variable_dto.name
        if pre_configuration_variable_dto.values:
            for value in pre_configuration_variable_dto.values:
                pre_configuration_variable_value_entity = PreConfigurationVariableValueEntity(
                    pre_configuration_variable_entity=self,
                    value=str(value),
                )
                session.add(pre_configuration_variable_value_entity)
    def to_json(self):
        return {
            "name": self.name,
            "values": [pre_configuration_variable_value_entity.value for pre_configuration_variable_value_entity in self.value_list],
        }

    def to_dto(self)->ConfigurationVariableDTO:
        return ConfigurationVariableDTO(
            name=self.name,
            values=[pre_configuration_variable_value_entity.value for pre_configuration_variable_value_entity in self.value_list],
        )
