from sqlalchemy import Column, String, Integer, Float, Text, ForeignKey
from sqlalchemy.orm import relationship
from storage.entity.base_entity import BaseEntity
import json
class RuleCollectInstructionMessageEntity(BaseEntity):
    __tablename__ = "rule_collect_instruction_message"
    role = Column(String(50), nullable=False)
    content = Column(Text, nullable=False)

    gpt_rule_collect_log_id = Column(Integer, ForeignKey("gpt_rule_collect_log.id"), nullable=False)
    gpt_rule_collect_log_entity = relationship("GPTRuleCollectLogEntity", back_populates="messages")


class GPTRuleCollectLogEntity(BaseEntity):
    __tablename__ = "gpt_rule_collect_log"
    object_name = Column(String(255), nullable=False)
    model = Column(String(255), nullable=False)
    timeout = Column(Integer, nullable=False)
    temperature = Column(Float, nullable=False)
    response = Column(Text, nullable=False)

    messages = relationship(
        "RuleCollectInstructionMessageEntity",
        back_populates="gpt_rule_collect_log_entity",
        cascade="all, delete-orphan"
    )

    mig_messages = relationship(
        "MigrateRuleCollectInstructionMessageEntity",
        back_populates="gpt_rule_collect_log_entity",
        cascade="all, delete-orphan"
    )

    rule_collect_id = Column(Integer, ForeignKey("rule_collect.id"))
    rule_collect_entity = relationship("RuleCollectEntity", back_populates="log_list")

    def __init__(self,
        rule_collect_entity,
        object_name: str,
        model: str,
        timeout: int,
        temperature: float,
        response: str,
        messages: list
    ):
        self.rule_collect_entity = rule_collect_entity
        self.object_name = object_name
        self.model = model
        self.timeout = timeout
        self.temperature = temperature
        self.response = response
        self.messages = [
            RuleCollectInstructionMessageEntity(
                gpt_rule_collect_log_entity=self,
                role=message.role,
                content=json.dumps(message.content) if isinstance(message.content, (list, dict)) else message.content
            ) for message in messages
        ]
