from sqlalchemy import Column, Integer, ForeignKey, Enum, Float
from sqlalchemy.orm import relationship
import enum

from dto.coverage_metric_dto import CoverageMetricDTO
from storage.entity.base_entity import BaseEntity
class CoverageType(enum.Enum):
    LINES = "L"
    STATEMENTS= "S"
    FUNCTIONS= "F"
    BRANCHES= "B"
    BRANCHES_TRUE= "BT"

class CoverageMetricEntity(BaseEntity):
    __tablename__ = "coverage_metric"
    type = Column(Enum(CoverageType), nullable=False)

    coverage_info_id = Column(Integer, ForeignKey("coverage_info.id"))
    coverage_info_entity = relationship("CoverageInfoEntity", back_populates="coverage_metric_list")

    total = Column(Integer, nullable=True)
    covered = Column(Integer, nullable=True)
    skipped = Column(Integer, nullable=True)
    pct = Column(Float, nullable=True)

    def __init__(self, coverage_metric_dto: CoverageMetricDTO, coverage_type:CoverageType, coverage_info_entity):
        super().__init__()
        self.type = coverage_type
        self.total = coverage_metric_dto.total
        self.covered = coverage_metric_dto.covered
        self.skipped = coverage_metric_dto.skipped
        self.pct = coverage_metric_dto.pct
        self.coverage_info_entity = coverage_info_entity
