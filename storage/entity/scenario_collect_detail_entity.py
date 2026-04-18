from dto.scenario_collect_dto import ScenarioCollectDTO
from dto.scenario_page_dto import ScenarioPageDTO
from storage.entity.base_entity import BaseEntity, session
from sqlalchemy import Column, String, Integer, ForeignKey
from sqlalchemy.orm import relationship

from storage.entity.pre_configuration_variable_entity import PreConfigurationVariableEntity
from storage.entity.scenario_entity import ScenarioEntity

class ScenarioCollectDetailEntity(BaseEntity):
    __tablename__ = 'scenario_collect_detail'

    scenario_collect_id = Column(Integer, ForeignKey("scenario_collect.id"))
    scenario_collect_entity = relationship("ScenarioCollectEntity", back_populates="detail_list")
    name = Column(String(255))
    description_type = Column(String(255))
    reference_value = Column(String(255))
    pre_configuration_variable_list = relationship(
        argument=PreConfigurationVariableEntity,
        back_populates="scenario_collect_detail_entity",
        cascade="all, delete-orphan"
    )
    scenario_list = relationship(
        argument=ScenarioEntity,
        back_populates="scenario_collect_detail_entity",
        cascade="all, delete-orphan"
    )

    def __init__(self, scenario_collect_entity, scenario_collect_dto: ScenarioCollectDTO, name:str, scenario_page_dto:ScenarioPageDTO):
        super().__init__()
        self.scenario_collect_entity = scenario_collect_entity
        self.name = name
        self.description_type = scenario_collect_dto.description_type.value
        self.reference_value = scenario_collect_dto.reference_value

        if scenario_collect_dto.scenario_list:
            for scenario_dto in scenario_collect_dto.scenario_list:
                scenario_entity = ScenarioEntity(scenario_collect_detail_entity = self,scenario_dto = scenario_dto)
                session.add(scenario_entity)

        if scenario_collect_dto.pre_configuration_variable_list:
            for pre_configuration_variable_dto in scenario_collect_dto.pre_configuration_variable_list:
                pre_configuration_variable_entity = PreConfigurationVariableEntity(scenario_collect_detail_entity = self,pre_configuration_variable_dto = pre_configuration_variable_dto)
                session.add(pre_configuration_variable_entity)

    def to_json(self):
        return {
            "description_type": self.description_type,
            "reference_value": self.reference_value,
            "scenario_list":[scenario.to_json() for scenario in self.scenario_list],
            "pre_configuration_variable_list": [pre_configuration_variable.to_json() for pre_configuration_variable in self.pre_configuration_variable_list]
        }

    def to_dto(self)->ScenarioCollectDTO:
        return ScenarioCollectDTO(
            description_type=self.description_type,
            reference_value=self.reference_value,
            scenario_list=[scenario.to_dto() for scenario in self.scenario_list],
            pre_configuration_variable_list=[pre_configuration_variable.to_dto() for pre_configuration_variable in self.pre_configuration_variable_list]
        )
