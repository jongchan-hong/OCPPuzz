from sqlalchemy import Column, String, Integer, ForeignKey, Enum
from sqlalchemy.orm import relationship
from storage.entity.base_entity import BaseEntity
from constants.fail_cause import FailCause


class RuleCollectFailEntity(BaseEntity):
    __tablename__ = "rule_collect_fail"

    message = Column(String(255), nullable=False)
    fail_cause = Column(Enum(FailCause), nullable=False)

    rule_collect_id = Column(Integer, ForeignKey("rule_collect.id"))

    rule_collect_entity = relationship("RuleCollectEntity", back_populates="fail_list")

    def __init__(self, rule_collect_entity, message: str = "", fail_cause: FailCause = FailCause.IMPOSSILBE):
        super().__init__()
        self.rule_collect_entity = rule_collect_entity
        self.message = message
        self.fail_cause = fail_cause