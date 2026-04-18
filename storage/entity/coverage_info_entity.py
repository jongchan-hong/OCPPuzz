from dto.coverage_info_dto import CoverageInfoDTO
from dto.coverage_metric_dto import CoverageMetricDTO
from storage.entity.base_entity import BaseEntity
from sqlalchemy import Column, String, Integer, ForeignKey
from sqlalchemy.orm import relationship
from storage.entity.coverage_metric_entity import CoverageMetricEntity, CoverageType

class CoverageInfoEntity(BaseEntity):
    __tablename__ = 'coverage_info'
    name = Column(String(100), nullable=False)
    coverage_metric_list = relationship(CoverageMetricEntity, back_populates="coverage_info_entity",
                               cascade="all, delete-orphan")
    test_execution_id = Column(Integer, ForeignKey("test_execution.id"))
    test_execution_entity = relationship("TestExecutionEntity", back_populates="coverage_info_entity")

    def __init__(self, name:str, coverage_info_dto: CoverageInfoDTO, test_execution_entity):
        super().__init__()
        self.name = name
        self.test_execution_entity = test_execution_entity
        if coverage_info_dto.lines:
            self.create_metric(coverage_metric_dto=coverage_info_dto.lines, coverage_type=CoverageType.LINES)
        if coverage_info_dto.statements:
            self.create_metric(coverage_metric_dto=coverage_info_dto.statements, coverage_type=CoverageType.STATEMENTS)
        if coverage_info_dto.functions:
            self.create_metric(coverage_metric_dto=coverage_info_dto.functions, coverage_type=CoverageType.FUNCTIONS)
        if coverage_info_dto.branches:
            self.create_metric(coverage_metric_dto=coverage_info_dto.branches, coverage_type=CoverageType.BRANCHES)
        if coverage_info_dto.branchesTrue:
            self.create_metric(coverage_metric_dto=coverage_info_dto.branchesTrue, coverage_type=CoverageType.BRANCHES_TRUE)

    def create_metric(self, coverage_metric_dto:CoverageMetricDTO, coverage_type:CoverageType):
        lines_coverage_metric_entity = CoverageMetricEntity(
            coverage_metric_dto=coverage_metric_dto,
            coverage_type=coverage_type,
            coverage_info_entity=self
        )
        self.coverage_metric_list.append(lines_coverage_metric_entity)