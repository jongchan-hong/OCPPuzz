from parser_modules.json.json_schema import JsonSchema
from scenario_collector_modules.scenario_act_type import ScenarioActType
from dataset.scripts.message_direction_result import MessageDirectionResult, MessageDirection
from parser_modules.parser import Parser
from dto.scenario_collect_dto import ScenarioCollectDTO, ScenarioDTO, \
    ConfigurationVariableDTO
from typing import Optional, Dict
from typing import List
from test_controller_modules.test_project_controller.citrine_event_controller import CitrineEventController

class ScenarioSet(set):
    PARTICIPANTS = ["CSMS", "Charging Station", "Local Controller"]

    def __init__(self, *args, parser:Parser = None, json_schemas:Dict[str, JsonSchema] = None):
        super().__init__(*args)
        self.parser = parser
        self.json_schemas = json_schemas
        self.invalid_variable_name_cnt = 0
        self.invalid_variable_values_cnt = 0
        self.invalid_supported_messages_cnt = 0
        self.invalid_available_participants_cnt = 0
        self.invalid_direction_cnt = 0
        self.invalid_fix_name_cnt = 0
        self.invalid_fix_value_enum_cnt = 0
        self.invalid_fix_value_id_cnt = 0
        self.invalid_fix_value_object_cnt = 0
        self.is_only_csms_to_cs_cnt = 0
        self.type_set = set()
        self.message_direction_result = MessageDirectionResult()
    def print_info(self):
        print("invalid_variable_name_cnt:", self.invalid_variable_name_cnt)
        print("invalid_variable_values_cnt:", self.invalid_variable_values_cnt)
        print("invalid_supported_messages_cnt:", self.invalid_supported_messages_cnt)
        print("invalid_direction_cnt:", self.invalid_direction_cnt)
        print("invalid_fix_name_cnt:", self.invalid_fix_name_cnt)
        print("invalid_fix_value_enum_cnt:", self.invalid_fix_value_enum_cnt)
        print("invalid_fix_value_id_cnt:", self.invalid_fix_value_id_cnt)
        print("invalid_fix_value_object_cnt:", self.invalid_fix_value_object_cnt)
        print("is_only_csms_to_cs_cnt:", self.is_only_csms_to_cs_cnt)



    def is_valid_scenario(self, scenario:ScenarioDTO)->bool:
        if not self.is_supported_message(scenario):
            self.invalid_supported_messages_cnt += 1
            return False
        if not self.is_available_participants(scenario):
            self.invalid_available_participants_cnt += 1
            return False
        if scenario.fix_value_list and not self.is_valid_fix_values(scenario):
            return False
        return True

    def is_supported_message(self, scenario:ScenarioDTO)->bool:
        return any (
            scenario.message == message.name
            for message in self.parser.messages
        )
    def is_available_participants(self, scenario: ScenarioDTO) -> bool:
        return (
            any(p in scenario.caller for p in self.PARTICIPANTS) and
            any(p in scenario.callee for p in self.PARTICIPANTS)
        )
    def is_valid_direction(self,scenario:ScenarioDTO)->bool:
        message_direction: Optional[MessageDirection] = self.message_direction_result.find_by_message_name(scenario.message)
        caller = scenario.caller
        callee = scenario.callee

        if "CSMS" in scenario.caller:
            caller = "CSMS"
        if "Charging Station" in scenario.caller:
            caller = "Charging Station"

        if "CSMS" in scenario.callee:
            callee = "CSMS"
        if "Charging Station" in scenario.callee:
            callee = "Charging Station"

        if "Local Controller" in scenario.caller and callee == "CSMS":
            caller = "Charging Station"

        if "Local Controller" in scenario.callee and caller == "CSMS":
            callee = "Charging Station"

        if not message_direction:
            return False
        return caller in message_direction.caller and callee in message_direction.callee

    def is_supported_csms_trigger(self, scenario:ScenarioDTO)->bool:
        return CitrineEventController.is_support_api(scenario.message)

    def is_valid_fix_values(self, scenario:ScenarioDTO) -> bool:
        json_schema = self.json_schemas.get(scenario.message)

        valid_fix_values = []

        for fix_value in scenario.fix_value_list:
            name_arr = fix_value.name.split(".")
            field_name = name_arr[-1]
            parent_field_name = None if len(name_arr) == 1 else name_arr[-2]
            data =  json_schema.get_data(field_name = field_name, parent_field_name = parent_field_name)
            if not data:
                self.invalid_fix_name_cnt += 1
                continue
            fix_value.parent_name = data.object_name
            self.type_set.add(data.value.type)

            if data.value.enum and fix_value.value not in data.value.enum:
                self.invalid_fix_value_enum_cnt += 1
                continue

            if fix_value.name.lower().endswith("id"):
                self.invalid_fix_value_id_cnt += 1
                continue
            try:
                match data.value.type:
                    case "object":
                        self.invalid_fix_value_object_cnt += 1
                        continue
                    case "boolean":
                        if isinstance(fix_value.value, str):
                            match fix_value.value.lower():
                                case "true":
                                    fix_value.value = True
                                case "false":
                                    fix_value.value = False
                                case _:
                                    self.invalid_fix_value_object_cnt += 1
                                    continue
                    case "integer":
                        fix_value.value = int(fix_value.value)
                    case "number":
                        fix_value.value = float(fix_value.value)
            except ValueError:
                self.invalid_fix_value_object_cnt += 1
                continue
            valid_fix_values.append(fix_value)
        scenario.fix_value_list = valid_fix_values
        return True

    def filter_valid_variables(self, variables:List[ConfigurationVariableDTO]):
        valid_variables = []
        for variable in variables:
            referenced_variable =self.parser.referenced_components_and_variables_parser.get_referenced_variable(variable.name)

            if not referenced_variable:
                self.invalid_variable_name_cnt += 1
                continue
            if not self.parser.referenced_components_and_variables_parser.is_valid_variable_values(variable):
                self.invalid_variable_values_cnt += 1
                continue
            variable.component_name = referenced_variable.get_component_name()
            variable.name = referenced_variable.get_variable_name()
            variable.datatype = referenced_variable.get_data_type()
            valid_variables.append(variable)
        variables.clear()
        variables.extend(valid_variables)
    def is_only_csms_to_cs(self, item: ScenarioCollectDTO):
        for scenario in item.scenario_list:
            if ScenarioActType.get_act_type(scenario) == ScenarioActType.CS_TO_CSMS_REQUEST:
                return False
        return True

    def get_valid_direction_scenario_dto(self, scenario_dto: ScenarioDTO)->Optional[ScenarioDTO]:
        message_direction: Optional[MessageDirection] = self.message_direction_result.find_by_message_name(scenario_dto.message)
        caller = scenario_dto.caller
        callee = scenario_dto.callee

        if "CSMS" in scenario_dto.caller:
            caller = "CSMS"
        if "Charging Station" in scenario_dto.caller:
            caller = "Charging Station"

        if "CSMS" in scenario_dto.callee:
            callee = "CSMS"
        if "Charging Station" in scenario_dto.callee:
            callee = "Charging Station"

        if "Local Controller" in scenario_dto.callee:
            callee = "Charging Station"
        if "Local Controller" in scenario_dto.caller:
            caller = "Charging Station"

        if not message_direction:
            return None

        if not (caller in message_direction.caller and callee in message_direction.callee):
            if len(message_direction.caller) == 0 or len(message_direction.callee) == 0:
                return scenario_dto

            scenario_dto.caller = message_direction.caller[0] if caller not in message_direction.caller else caller
            scenario_dto.callee = message_direction.callee[0] if callee not in message_direction.callee else callee

            self.invalid_direction_cnt += 1
        return scenario_dto


    def add(self, item: ScenarioCollectDTO):
        if self.is_only_csms_to_cs(item):
            self.is_only_csms_to_cs_cnt += 1
            return
        self.filter_valid_variables(item.pre_configuration_variable_list)
        corrected: list[ScenarioDTO] = []

        for scenario_dto in item.scenario_list:
            scenario_dto = self.get_valid_direction_scenario_dto(scenario_dto)
            if not scenario_dto:
                return
            if not self.is_valid_scenario(scenario_dto):
                return

        super().add(item)

    def get_result(self):
        return [item.to_json() for item in self]
