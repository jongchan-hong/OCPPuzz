class ReferencedVariable(object):
    def __init__(self, name, tables):
        self.name = name
        self.tables = tables
        self.data = self.to_dict()
    def get_instruction_content(self):
        result = {
            "name": self.name,
            "componentName": self.get_component_name(),
            "variableName": self.get_variable_name()
        }

        data_type = self.get_data_type()
        if data_type:
            result["dataType"] = data_type

        return result

    def get_description(self):
        if "Description" in self.data:
            return self.data["Description"]

    def get_data_type(self):
        if self.data:
            if "Variable" in self.data and "variableCharacteristics" in self.data["Variable"] and "dataType" in self.data["Variable"]["variableCharacteristics"]:
                return self.data["Variable"]["variableCharacteristics"]["dataType"]
        return None

    def get_value_list(self):
        if self.data:
            if "Variable" in self.data and "variableCharacteristics" in self.data["Variable"] and "valueList" in self.data["Variable"]["variableCharacteristics"]:
                return self.data["Variable"]["variableCharacteristics"]["valueList"]
            if "Variable" in self.data and "variableCharacteristics" in self.data["Variable"] and "valuesList" in self.data["Variable"]["variableCharacteristics"]:
                return self.data["Variable"]["variableCharacteristics"]["valuesList"]
        return None

    def get_variable_name(self):
        if self.data and "Variable" in self.data and "variableName" in self.data["Variable"]:
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