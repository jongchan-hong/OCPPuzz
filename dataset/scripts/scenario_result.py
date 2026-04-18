import os
import json

from dto.scenario_collect_dto import ScenarioCollectDTO
from scenario_collector_modules.scenario_set import ScenarioSet

class ScenarioResult:
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    FILE_PATH = os.path.join(BASE_DIR, "scenario_result.json")

    def load(self):
        with open(self.FILE_PATH, "r", encoding="utf-8") as f:
            raw_data = json.load(f)
        return [ScenarioCollectDTO(**item) for item in raw_data]

    def get_scenario_set(self, parser, json_schemas):
        self.scenarios = self.load()
        scenario_set = ScenarioSet(parser=parser, json_schemas=json_schemas)
        for scenario_collect_dto in self.scenarios:
            scenario_set.add(scenario_collect_dto)
        scenario_set.print_info()
        return scenario_set