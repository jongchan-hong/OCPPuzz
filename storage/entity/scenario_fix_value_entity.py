from dto.scenario_collect_dto import FixValue
from storage.entity.base_entity import BaseEntity
from sqlalchemy import Column, String, Integer, ForeignKey
from sqlalchemy.orm import relationship


class ScenarioFixValueEntity(BaseEntity):
    __tablename__ = 'scenario_fix_value'

    name = Column(String(255), nullable=False)
    value = Column(String(255))

    scenario_id = Column(Integer, ForeignKey("scenario.id"))
    scenario_entity = relationship("ScenarioEntity", back_populates="fix_value_list")

    def to_json(self):
        return {
            "name": self.name,
            "value": self.value,
        }

    def to_dto(self) -> FixValue:
        return FixValue(
            name=self.name,
            value=self.value,
        )
