from sqlalchemy.orm import relationship
from storage.entity.base_entity import BaseEntity
from sqlalchemy import Column, String

from storage.entity.generate_message_entity import GenerateMessageEntity
from storage.entity.generate_message_fail_entity import GenerateMessageFailEntity
from storage.entity.test_coverage_entity import TestCoverageEntity


class TestEntity(BaseEntity):
    __tablename__ = 'test'
    cause = Column(String(255))

    generate_message_list = relationship(
        argument=GenerateMessageEntity,
        back_populates="test_entity",
        cascade="all, delete-orphan"
    )

    generate_message_fail_list = relationship(
        argument=GenerateMessageFailEntity,
        back_populates="test_entity",
        cascade="all, delete-orphan"
    )

    test_coverage_list = relationship(
        argument=TestCoverageEntity,
        back_populates="test_entity",
        cascade="all, delete-orphan"
    )

