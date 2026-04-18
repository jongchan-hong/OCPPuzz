from dto.scenario_collect_dto import ScenarioDTO
from storage.entity.base_entity import BaseEntity, session
from sqlalchemy import Column, String, Integer, ForeignKey
from sqlalchemy.orm import relationship

from storage.entity.scenario_fix_value_entity import ScenarioFixValueEntity


class ScenarioEntity(BaseEntity):
    __tablename__ = 'scenario'

    scenario_collect_detail_id = Column(Integer, ForeignKey('scenario_collect_detail.id'))
    scenario_collect_detail_entity = relationship(
        argument="ScenarioCollectDetailEntity",
        back_populates="scenario_list"
    )
    caller = Column(String(100))
    callee = Column(String(100))
    message = Column(String(100))

    fix_value_list = relationship(
        argument=ScenarioFixValueEntity,
        back_populates="scenario_entity",
        cascade="all, delete-orphan"
    )

    def __init__(self, scenario_collect_detail_entity, scenario_dto: ScenarioDTO):
        super().__init__()
        self.scenario_collect_detail_entity = scenario_collect_detail_entity
        self.caller = scenario_dto.caller
        self.callee = scenario_dto.callee
        self.message = scenario_dto.message

        if scenario_dto.fix_value_list:
            for fix_value in scenario_dto.fix_value_list:
                scenario_fix_value_entity = ScenarioFixValueEntity(
                    scenario_entity=self,
                    value=str(fix_value.value),
                    name=str(fix_value.name),
                )
                session.add(scenario_fix_value_entity)

    def to_dto(self) -> ScenarioDTO:
        return ScenarioDTO(
            caller=self.caller,
            callee=self.callee,
            message=self.message,
            fix_value_list=[scenario_fix_value_entity.to_dto() for scenario_fix_value_entity in self.fix_value_list]
        )

    def to_json(self):
        return {
            "caller": self.caller,
            "callee": self.callee,
            "message": self.message,
            "fix_value_list": [fix_value.to_json() for fix_value in self.fix_value_list]
        }