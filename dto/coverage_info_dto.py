from typing import Optional

from pydantic import BaseModel, ConfigDict

from dto.coverage_metric_dto import CoverageMetricDTO

class CoverageInfoDTO(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    lines: Optional[CoverageMetricDTO]
    statements: Optional[CoverageMetricDTO]
    functions: Optional[CoverageMetricDTO]
    branches: Optional[CoverageMetricDTO]
    branchesTrue: Optional[CoverageMetricDTO]