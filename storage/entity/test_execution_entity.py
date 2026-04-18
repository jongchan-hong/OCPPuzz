from sqlalchemy.orm import relationship
from storage.entity.base_entity import BaseEntity
from sqlalchemy import Column, String, Integer, ForeignKey, DateTime
from sqlalchemy.dialects.mysql import JSON

from storage.entity.coverage_info_entity import CoverageInfoEntity


class TestExecutionEntity(BaseEntity):
    __tablename__ = 'test_execution'

    generate_message_id = Column(Integer, ForeignKey("generate_message.id"))
    generate_message_entity = relationship("GenerateMessageEntity", back_populates="test_execution_list")

    response = Column(JSON)
    error_name = Column(String(255))
    send_at = Column(DateTime)
    response_at = Column(DateTime)
    project_name = Column(String(255))

    coverage_info_entity = relationship(
        argument=CoverageInfoEntity,
        back_populates="test_execution_entity",
        uselist=False
    )

