from storage.entity.base_entity import BaseEntity
from sqlalchemy import Column, String
from sqlalchemy.orm import relationship

from storage.entity.gpt_scenario_collect_log_entity import GPTScenarioCollectLogEntity
from storage.entity.scenario_collect_detail_entity import ScenarioCollectDetailEntity
from storage.entity.scenario_collect_fail_entity import ScenarioCollectFailEntity
from util.hash import calculate_sha256


class ScenarioCollectEntity(BaseEntity):
    __tablename__ = 'scenario_collect'

    file_path = Column(String(255), nullable=False)
    check_sum_hash = Column(String(255), nullable=False, default="")
    detail_list = relationship(ScenarioCollectDetailEntity, back_populates="scenario_collect_entity",
                               cascade="all, delete-orphan")
    log_list = relationship(GPTScenarioCollectLogEntity, back_populates="scenario_collect_entity",
                            cascade="all, delete-orphan")
    fail_list = relationship(ScenarioCollectFailEntity, back_populates="scenario_collect_entity",
                             cascade="all, delete-orphan")

    def __init__(self, file_path: str):
        super().__init__()
        self.file_path = file_path
        self.check_sum_hash = calculate_sha256(file_path)