from enum import Enum, auto

from constants.ocpp_version import OcppVersion
from constants.parse_mode import ParseMode
from ordered_set import OrderedSet

class Variable():
    def __init__(self, name, tables):
        self.name = name
        self.tables = tables
        self.data = self.to_dict()

    def get_variable_name(self):
        if self.data:
            return self.data["Variable"]["variableName"]
        return None

    def get_component_name(self):
        if self.data and "Component" in self.data and "componentName" in self.data["Component"]:
            return self.data["Component"]["componentName"]
        return None

    def to_dict(self):
        result = {}
        last_value = {}
        full_value_list = []
        for table in self.tables:
            rows = table.extract()
            for row in rows:
                if len(row) == 4:
                    full_value = []
                    for index, data in enumerate(row):
                        if data is not None:
                            last_value[index] = data
                            keys_to_delete = [k for k in last_value if k > index]
                            for k in keys_to_delete:
                                del last_value[k]
                            full_value.append(data)
                        else:
                            if index in last_value:
                                full_value.append(last_value[index])
                    full_value_list.append(full_value)
        for full_value in full_value_list:
            if len(full_value) >= 2:
                self.set_nested_value(result, full_value[:-1], full_value[-1])
        return result

    def set_nested_value(self, result, keys, value):
        cur = result
        for key in keys[:-1]:
            cur = cur.setdefault(key, {})
        cur[keys[-1]] = value

    def value_exist(self, index, row):
        for idx, ch in enumerate(row, start=index):
            if ch is not None:
                return True
        return False




class Value():
    def __init__(self, name, tables):
        self.name = name
        self.tables = tables
class Mode(Enum):
    VARIABLE_MODE = auto()
    VALUES_MODE = auto()

def get_variables_and_values_from_pages(version, pages, config):
    if version == OcppVersion.version_160:
        return None
    variables = []
    values = []
    save_tables = OrderedSet()
    current_value= None
    mode = Mode.VARIABLE_MODE
    for index, page in enumerate(pages):
        y_min = 0
        if not page.extract_text():
            continue
        words = page.extract_words()
        tables = page.find_tables()
        current_word = None
        for word in words:
            if 819 < word["top"] < 820 or word["top"] < 11.44:
                continue

            if is_value_name(config, word) or is_variable_name(config, word):
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
                        variables.append(Variable(current_value , save_tables))
                    elif mode == Mode.VALUES_MODE:
                        values.append(Value(current_value, save_tables))
                    save_tables = OrderedSet()

                if is_variable_name(config, word):
                    mode = Mode.VARIABLE_MODE
                elif is_value_name(config, word):
                    mode = Mode.VALUES_MODE
                current_value = word["text"]
                current_word = word
                y_min = word["top"]

            if round(word["height"]) == 9 and word["text"] in ["Required", "Component", "Variable", "Description"]:
                for table in tables:
                    if table.bbox[1] > y_min:
                        save_tables.add(table)
                        break

        if index == len(pages) - 1 and current_value:
            save_tables.add(tables[-1])
            if mode == Mode.VARIABLE_MODE:
                variables.append(Variable(current_value, save_tables))
            elif mode == Mode.VALUES_MODE:
                values.append(Value(current_value, save_tables))

    return variables, values


def is_variable_name(config, word):
    return (round(word["height"]) == config["size"]["level_3_height"]
            and not word["text"].endswith(".")
            and word["text"] != "values")


def is_value_name(config, word):
    return (round(word["height"]) == config["size"]["level_4_height"]
            and not word["text"].endswith(".")
            and word["text"] != "values")