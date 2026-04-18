from enum import Enum, auto

from dto.scenario_collect_dto import ScenarioDTO

class ScenarioActType(Enum):
    CS_TO_CSMS_REQUEST = auto()
    CS_TO_CSMS_RESPONSE = auto()
    CSMS_TO_CS_REQUEST = auto()
    CSMS_TO_CS_RESPONSE = auto()

    @staticmethod
    def get_act_type(scenario_dto:ScenarioDTO):
        if "Local Controller" in scenario_dto.caller:
            if "CSMS" in scenario_dto.callee:
                if scenario_dto.message.endswith("Request"):
                    return ScenarioActType.CS_TO_CSMS_REQUEST
                else:
                    return ScenarioActType.CS_TO_CSMS_RESPONSE
        if "Charging Station" in scenario_dto.caller:
            if "CSMS" in scenario_dto.callee:
                if scenario_dto.message.endswith("Request"):
                    return ScenarioActType.CS_TO_CSMS_REQUEST
                else:
                    return ScenarioActType.CS_TO_CSMS_RESPONSE
        if "CSMS" in scenario_dto.caller:
            if "Charging Station" in scenario_dto.callee or "Local Controller" in scenario_dto.callee:
                if scenario_dto.message.endswith("Request"):
                    return ScenarioActType.CSMS_TO_CS_REQUEST
                else:
                    return ScenarioActType.CSMS_TO_CS_RESPONSE
        return None