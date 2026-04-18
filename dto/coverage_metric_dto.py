from pydantic import BaseModel
class CoverageMetricDTO(BaseModel):
    total: int
    covered: int
    skipped: int
    pct: float