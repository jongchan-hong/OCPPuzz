import json
class FixValueContainer:
    def __init__(self):
        self.data = {}

    def set_value(self, parent_key, field_name, value):
        self.data[(parent_key, field_name)] = value

    def get_value(self, parent_key, field_name):
        return self.data.get((parent_key, field_name), None)

    def del_value(self, parent_key, field_name):
        self.data.pop((parent_key, field_name), None)

    def to_dict(self):
        result = {}
        for (parent_key, field_name), value in self.data.items():
            if parent_key not in result:
                result[parent_key] = {}
            result[parent_key][field_name] = value
        return result

    def to_json(self, indent=None):
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=indent)

    @staticmethod
    def from_dict(data_dict):
        container = FixValueContainer()
        for compound_key, value in data_dict.items():
            parent_key, field_name = compound_key.split("::", 1)
            container.set_value(parent_key, field_name, value)
        return container