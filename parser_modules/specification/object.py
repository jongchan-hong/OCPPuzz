from typing import List, Dict
import json

from parser_modules.json.json_schema import PropertyType
from parser_modules.specification.field import Field

class Object:
    def __init__(self, name, description, field_tables):
        self.name = name
        self.description = description
        self.field_tables = field_tables

        self.fields: List[Field] = []
        for table in self.field_tables:
            rows = table.extract()
            for row in rows:
                if row[0] == "Field Name":
                    continue
                field = Field(row)
                self.fields.append(field)

    def get_information(self, parser, json_description, properties: Dict[str, PropertyType]):
        result = {}
        result['object_name'] = self.name
        result['object_description'] = self.description
        result['json_description'] = json_description
        result['fields'] = []
        for field in self.fields:
            information = field.get_information(parser)
            if properties:
                property = properties.get(field.name)
                if property and property.minItems:
                    if int(field.min_size) != int(property.minItems):
                        print(f"{self.name}\t{field.name}\t{field.card}\t{property.minItems}\t{property.maxItems}")
                if property is not None and property.description:
                    information["json_description"] = property.description
            result['fields'].append(information)
        return json.dumps(result)