from dataclasses import dataclass
@dataclass
class TotalCoverageDTO:
    total_statements: int
    covered_statements: int
    total_branches: int
    covered_branches: int