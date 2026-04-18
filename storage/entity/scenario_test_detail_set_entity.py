from sqlalchemy.orm import relationship
from storage.entity.base_entity import BaseEntity
from sqlalchemy import Column, String, Integer, ForeignKey

from storage.entity.generate_message_entity import GenerateMessageEntity


class ScenarioTestDetailSetEntity(BaseEntity):
    __tablename__ = 'scenario_test_detail_set'

    scenario_test_detail_id = Column(Integer, ForeignKey("scenario_test_detail.id"))
    scenario_test_detail_entity = relationship("ScenarioTestDetailEntity", back_populates="scenario_test_detail_set_entity_list")
    fail_cause = Column(String(255))
    
    generate_message_list = relationship(
        argument=GenerateMessageEntity,
        back_populates="scenario_test_detail_set_entity",
        cascade="all, delete-orphan"
    )