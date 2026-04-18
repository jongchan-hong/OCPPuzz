from sqlalchemy.dialects.mysql import LONGTEXT
from sqlalchemy.orm import relationship
from storage.entity.base_entity import BaseEntity
from sqlalchemy import Column, String, Integer, ForeignKey

from storage.entity.scenario_test_detail_set_entity import ScenarioTestDetailSetEntity


class ScenarioTestDetailEntity(BaseEntity):
    __tablename__ = 'scenario_test_detail'

    scenario_test_id = Column(Integer, ForeignKey("scenario_test.id"))
    scenario_test_entity = relationship("ScenarioTestEntity", back_populates="scenario_test_detail_list")
    pre_configuration = Column(LONGTEXT, nullable=True)
    scenario_collect_info = Column(LONGTEXT, nullable=True)
    fail_cause = Column(String(255))

    scenario_test_detail_set_entity_list = relationship(
        argument=ScenarioTestDetailSetEntity,
        back_populates="scenario_test_detail_entity",
        cascade="all, delete-orphan"
    )