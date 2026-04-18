from sqlalchemy import Column, String, Integer, Float, Text, ForeignKey
from sqlalchemy.orm import relationship
from storage.entity.base_entity import BaseEntity
import json
class ScenarioCollectInstructionMessageEntity(BaseEntity):
    __tablename__ = "scenario_collect_instruction_message"
    role = Column(String(50), nullable=False)
    content = Column(Text, nullable=False)

    gpt_scenario_collect_log_id = Column(Integer, ForeignKey("gpt_scenario_collect_log.id"), nullable=False)
    gpt_scenario_collect_log_entity = relationship("GPTScenarioCollectLogEntity", back_populates="messages")


class GPTScenarioCollectLogEntity(BaseEntity):
    __tablename__ = "gpt_scenario_collect_log"
    object_name = Column(String(255), nullable=False)
    model = Column(String(255), nullable=False)
    timeout = Column(Integer, nullable=False)
    temperature = Column(Float, nullable=False)
    response = Column(Text, nullable=False)

    messages = relationship(
        "ScenarioCollectInstructionMessageEntity",
        back_populates="gpt_scenario_collect_log_entity",
        cascade="all, delete-orphan"
    )

    mig_messages = relationship(
        "MigrateScenarioCollectInstructionMessageEntity",
        back_populates="gpt_scenario_collect_log_entity",
        cascade="all, delete-orphan"
    )

    scenario_collect_id = Column(Integer, ForeignKey("scenario_collect.id"))
    scenario_collect_entity = relationship("ScenarioCollectEntity", back_populates="log_list")

    def __init__(self,
        scenario_collect_entity,
        object_name: str,
        model: str,
        timeout: int,
        temperature: float,
        response: str,
        messages: list
    ):
        self.scenario_collect_entity = scenario_collect_entity
        self.object_name = object_name
        self.model = model
        self.timeout = timeout
        self.temperature = temperature
        self.response = response
        self.messages = [
            ScenarioCollectInstructionMessageEntity(
                gpt_scenario_collect_log_entity=self,
                role=message.role,
                content=json.dumps(message.content) if isinstance(message.content, (list, dict)) else message.content
            ) for message in messages
        ]
