from sqlalchemy import ForeignKey, Integer, Column, String, Text
from sqlalchemy.orm import relationship
from storage.entity.base_entity import BaseEntity


class MigrateRuleCollectInstructionMessageEntity(BaseEntity):
    __tablename__ = "mig_rule_collect_instruction_message"
    role = Column(String(50), nullable=False)
    content = Column(Text, nullable=False)

    gpt_rule_collect_log_id = Column(Integer, ForeignKey("gpt_rule_collect_log.id"), nullable=False)
    gpt_rule_collect_log_entity = relationship("GPTRuleCollectLogEntity", back_populates="mig_messages")

    @classmethod
    def from_entity(cls, src: "RuleCollectInstructionMessageEntity"):
        return cls(
            role=src.role,
            content=src.content,
            gpt_rule_collect_log_id=src.gpt_rule_collect_log_id,
            gpt_rule_collect_log_entity=src.gpt_rule_collect_log_entity,
            created_at=src.created_at,
        )

    def __init__(self, role, content, gpt_rule_collect_log_id, gpt_rule_collect_log_entity, created_at):
        self.role = role
        self.content = content
        self.gpt_rule_collect_log_id = gpt_rule_collect_log_id
        self.gpt_rule_collect_log_entity = gpt_rule_collect_log_entity
        self.created_at = created_at