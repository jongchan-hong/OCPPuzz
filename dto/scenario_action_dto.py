from scenario_collector_modules.scenario_act_type import ScenarioActType
from generator_modules.generator import Generator


class ScenarioActionDTO:
    def __init__(self, generator: Generator, scenario_act_type: ScenarioActType):
        self.generator = generator
        self.scenario_act_type = scenario_act_type