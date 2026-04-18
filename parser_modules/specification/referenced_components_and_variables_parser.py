from enum import Enum, auto
from typing import List, Optional
import json
from ordered_set import OrderedSet
from pdfplumber.page import Page

from dto.scenario_collect_dto import ConfigurationVariableDTO
from parser_modules.specification.referenced_variable import ReferencedVariable
from parser_modules.specification.referenced_variable_value import ReferencedVariableValue


class Mode(Enum):
    VARIABLE_MODE = auto()
    VALUES_MODE = auto()

class ReferencedComponentsAndVariablesParser:

    def __init__(self, pages:List[Page], config):
        self.pages = pages
        self.config = config
        self.variable_list, self.variable_value_list = self.collect()
    def get_instruction_content(self):
        return json.dumps([referenced_variable.get_instruction_content() for referenced_variable in self.variable_list], ensure_ascii=False)

    def is_variable_name(self, word):
        return (round(word["height"]) == self.config["size"]["level_3_height"]
                and not word["text"].endswith(".")
                and word["text"] != "values")

    def is_value_name(self, word):
        return (round(word["height"]) == self.config["size"]["level_4_height"]
                and not word["text"].endswith(".")
                and word["text"] != "values")

    def get_referenced_variable(self, name) -> ReferencedVariable:
        name_arr = name.split(".")
        variable_name = None
        component_name = None

        if len(name_arr) > 1:
            component_name = name_arr[0]
            variable_name = name_arr[1]
        else:
            variable_name = name_arr[0]

        for variable in self.variable_list:
            if name == variable.name:
                return variable

        for variable in self.variable_list:
            if variable_name == variable.get_variable_name():
                if component_name and component_name != variable.get_component_name():
                    continue
                return variable
        return None

    def is_valid_variable_name(self, name):
        name = name.split(".")[-1]
        return any(
            name == variable.name or name == variable.get_variable_name() or name.split(".")[-1] == variable.get_variable_name()
            for variable in self.variable_list
        )
    def get_component_name_and_variable_name_from_str(self, name):
        value_arr = name.split(".")
        component_name = None
        if len(value_arr) > 1:
            component_name = value_arr[-2]
        variable_name = value_arr[-1]
        return component_name, variable_name

    def get_variable_by_name(self, name: str) -> Optional[ReferencedVariable]:
        component_name, variable_name = self.get_component_name_and_variable_name_from_str(name)
        for variable in self.variable_list:
            if component_name and variable.get_component_name() == component_name:
                if variable.get_variable_name() == variable_name:
                    return variable
            if variable.name == variable_name:
                return variable
        return None

    def is_valid_variable_values(self, configuration_variable_dto : ConfigurationVariableDTO):
        standardized_variable = self.get_variable_by_name(configuration_variable_dto.name)
        if standardized_variable is None:
            return False
        try:
            match standardized_variable.get_data_type():
                case "decimal":
                    for value in configuration_variable_dto.values:
                        float(value)
                case "boolean":
                    for value in configuration_variable_dto.values:
                        if value.lower() not in ["true", "false"]:
                            return False
                case "integer":
                    for value in configuration_variable_dto.values:
                        int(value)
                case "OptionList":
                    value_list = [v.strip() for v in standardized_variable.get_value_list().split(",")]
                    for value in configuration_variable_dto.values:
                        if value not in value_list:
                            return False
                case "string":
                    for value in configuration_variable_dto.values:
                        str(value)
                case "dateTime":
                    pass
                case "MemberList":
                    pass
                case _:
                    exit(333333)
        except ValueError:
            return False
        return True


    def collect(self):
        variables = []
        values = []
        save_tables = OrderedSet()
        current_value= None
        mode = Mode.VARIABLE_MODE
        for index, page in enumerate(self.pages):
            y_min = 0
            if not page.extract_text():
                continue
            words = page.extract_words()
            tables = page.find_tables()
            current_word = None
            for word in words:
                if 819 < word["top"] < 820 or word["top"] < 11.44:
                    continue

                if self.is_value_name(word) or self.is_variable_name(word):
                    if current_word and current_word["top"] == word["top"]:
                        current_value = current_value +" "+word["text"]
                        continue
                    if current_value:
                        if y_min == 0:
                            for table in tables:
                                if table.bbox[1] < word["top"]:
                                    save_tables.add(table)
                                    break
                        if mode == Mode.VARIABLE_MODE:
                            variables.append(ReferencedVariable(current_value , save_tables))
                        elif mode == Mode.VALUES_MODE:
                            values.append(ReferencedVariableValue(current_value, save_tables))
                        save_tables = OrderedSet()

                    if self.is_variable_name(word):
                        mode = Mode.VARIABLE_MODE
                    elif self.is_value_name(word):
                        mode = Mode.VALUES_MODE
                    current_value = word["text"]
                    current_word = word
                    y_min = word["top"]

                if round(word["height"]) == 9 and word["text"] in ["Required", "Component", "Variable", "Description"]:
                    for table in tables:
                        if table.bbox[1] > y_min:
                            save_tables.add(table)
                            break

            if index == len(self.pages) - 1 and current_value:
                save_tables.add(tables[-1])
                if mode == Mode.VARIABLE_MODE:
                    variables.append(ReferencedVariable(current_value, save_tables))
                elif mode == Mode.VALUES_MODE:
                    values.append(ReferencedVariableValue(current_value, save_tables))

        return variables, values
