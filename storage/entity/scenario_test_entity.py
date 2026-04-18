from sqlalchemy.orm import relationship
from storage.entity.base_entity import BaseEntity

from storage.entity.scenario_test_detail_entity import ScenarioTestDetailEntity


class ScenarioTestEntity(BaseEntity):
    __tablename__ = 'scenario_test'

    scenario_test_detail_list = relationship(
        argument=ScenarioTestDetailEntity,
        back_populates="scenario_test_entity",
        cascade="all, delete-orphan"
    )