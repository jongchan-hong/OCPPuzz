from sqlalchemy import Column, String, Integer, ForeignKey, Enum
from sqlalchemy.orm import relationship
from storage.entity.base_entity import BaseEntity
from constants.fail_cause import FailCause


class ScenarioCollectFailEntity(BaseEntity):
    __tablename__ = "scenario_collect_fail"

    name = Column(String(255), nullable=False)
    fail_cause = Column(Enum(FailCause), nullable=False)
    scenario_collect_id = Column(Integer, ForeignKey("scenario_collect.id"))
    scenario_collect_entity = relationship("ScenarioCollectEntity", back_populates="fail_list")