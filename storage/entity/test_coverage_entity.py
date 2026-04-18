from sqlalchemy.orm import relationship

from dto.total_coverage_dto import TotalCoverageDTO
from storage.entity.base_entity import BaseEntity
from sqlalchemy import Column, String, Integer, ForeignKey


class TestCoverageEntity(BaseEntity):
    __tablename__ = 'test_coverage'

    test_id = Column(Integer, ForeignKey("test.id"))
    test_entity = relationship("TestEntity", back_populates="test_coverage_list")

    project_name = Column(String(255))
    total_statements = Column(Integer, nullable=True)
    covered_statements = Column(Integer, nullable=True)
    total_branches = Column(Integer, nullable=True)
    covered_branches = Column(Integer, nullable=True)

    def __init__(self, test_entity, project_name, total_coverage_dto:TotalCoverageDTO):
        super().__init__()
        self.test_id = test_entity.id
        self.test_entity = test_entity
        self.project_name = project_name
        self.total_statements = total_coverage_dto.total_statements
        self.covered_statements = total_coverage_dto.covered_statements
        self.total_branches = total_coverage_dto.total_branches
        self.covered_branches = total_coverage_dto.covered_branches