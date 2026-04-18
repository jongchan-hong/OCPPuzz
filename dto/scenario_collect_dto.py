import random
import sys
from enum import Enum
from typing import List, Optional, Any
from pydantic import BaseModel

from generator_modules.fix_value_container import FixValueContainer
from dto.constraint_collect_dto import AdditionalPageRequest
import string

class FixValue(BaseModel):
    parent_name: Optional[str] = None
    name:str
    value:Optional[Any]= None
    def __eq__(self, other):
        if self.name != other.name:
            return False
        if self.value != other.value:
            return False
        return True
    def __hash__(self):
        return hash((self.name, self.value))

class ScenarioDTO(BaseModel):
    caller: str
    callee: str
    message: str
    fix_value_list: Optional[List[FixValue]] = None

    def __eq__(self, other):
        if self.caller != other.caller:
            return False
        if self.callee != other.callee:
            return False
        if self.message != other.message:
            return False

        if self.fix_value_list is None or other.fix_value_list is None:
            if self.fix_value_list != other.fix_value_list:
                return False
        elif len(self.fix_value_list) != len(other.fix_value_list):
            return False

        if set(self.fix_value_list or []) != set(other.fix_value_list or []):
            return False
        return True
    def __hash__(self):
        return hash((
            self.caller,
            self.callee,
            self.message,
            frozenset(self.fix_value_list or [])
        ))

    def to_json(self):
        return self.model_dump()

    def get_fix_value_container(self):
        fix_value_container = FixValueContainer()
        for fix_value in self.fix_value_list:
            fix_value_container.set_value(fix_value.parent_name, fix_value.name, fix_value.value)
        return fix_value_container


class ScenarioDescriptionType(Enum):
    SCENARIO_DESCRIPTION = "main"
    ALTERNATIVE_DESCRIPTION = "alternative"
    COMBINED_DESCRIPTION = "combined"

class ConfigurationVariableDTO(BaseModel):
    datatype: Optional[str] = None
    component_name: Optional[str] = None
    name: str
    values: Optional[List[str]] = None

    def __eq__(self, other):
        if self.component_name != other.component_name:
            return False
        if self.name != other.name:
            return False
        if self.values is None or other.values is None:
            if self.values != other.values:
                return False
        elif len(self.values) != len(other.values):
            return False
        if set(self.values or []) != set(other.values or []):
            return False
        return True
    def __hash__(self):
        return hash((
            self.component_name,
            self.name,
            frozenset(self.values or [])
        ))

    def to_set_variable_data(self):
        value = None
        if self.values:
            if len(self.values) > 1:
                value = ",".join(str(v) for v in self.values)
            elif len(self.values) == 1:
                value = self.values[0]
        if value is None:
            match self.datatype:
                case "boolean":
                    value = "true"
                case "integer":
                    value =str(random.randint(0, sys.maxsize))
                case "string":
                    value = ''.join(random.sample(string.ascii_uppercase, 10))
                case _:
                    print("need to_set_variable_data ",self.datatype)
            pass

        return {
            "attributeValue":value,
            "component": {
                "name":self.component_name
            },
            "variable": {
                "name": self.name
            }
        }

class ScenarioCollectDTO(BaseModel):
    description_type:ScenarioDescriptionType
    reference_value:Optional[str]= None
    scenario_list: Optional[List[ScenarioDTO]] = None
    pre_configuration_variable_list: Optional[List[ConfigurationVariableDTO]] = []

    def __eq__(self, other):
        if self.reference_value != other.reference_value:
            return False
        if self.scenario_list is None or other.scenario_list is None:
            if self.scenario_list != other.scenario_list:
                return False
        elif len(self.scenario_list) != len(other.scenario_list):
            return False
        for a, b in zip(self.scenario_list, other.scenario_list):
            if a != b:
                return False
        if self.pre_configuration_variable_list is None or other.pre_configuration_variable_list is None:
            if self.pre_configuration_variable_list != other.pre_configuration_variable_list:
                return False
        elif len(self.pre_configuration_variable_list) != len(other.pre_configuration_variable_list):
            return False
        if set(self.pre_configuration_variable_list or []) != set(other.pre_configuration_variable_list or []):
            return False
        return True

    def __hash__(self):
        return hash((
            self.reference_value,
            frozenset(self.scenario_list or []),
            frozenset(self.pre_configuration_variable_list or [])
        ))

    def to_json(self):
        return self.model_dump_json()

    def get_set_variable_data_list(self):
        return [v.to_set_variable_data() for v in self.pre_configuration_variable_list]

class AdditionalInfoRequest(BaseModel):
    additional_schema_message_list: Optional[List[str]] = None
    additional_page_request_list: Optional[List[AdditionalPageRequest]] = None

class ScenarioCollectResult(BaseModel):
    additional_info_request: Optional[AdditionalInfoRequest] = None
    scenario_collect_list: Optional[List[ScenarioCollectDTO]] = None
