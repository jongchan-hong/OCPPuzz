from pydantic import BaseModel

class ScenarioPageDTO(BaseModel):
    scenario_name: str
    start_index: int
    end_index: int
    figure_line: str