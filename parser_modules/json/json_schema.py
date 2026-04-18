import json
import re
from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Dict, ForwardRef, Any
from pathlib import Path
from deepdiff import DeepDiff

from rule_collector_modules.rule_set import RuleSet
from dto.constraint_collect_dto import Rule, Cause
from storage.entity.base_entity import session
from storage.entity.rule_collect_detail_entity import RuleCollectDetailEntity

class EnumType(BaseModel):
    description: Optional[str] = None
    values: List[str]
PropertyTypeRef = ForwardRef('PropertyType')

class PropertyType(BaseModel):
    type: Optional[str] = None
    description: Optional[str] = None
    maxLength: Optional[int] = None
    minLength: Optional[int] = None
    minItems: Optional[int] = None
    maxItems: Optional[int] = None
    items: Optional[PropertyTypeRef] = None
    ref: Optional[str] = Field(None, alias="$ref")
    additionalProperties: Optional[bool] = None
    enum: Optional[List[str]] = None
    minimum: Optional[int] = None
    maximum: Optional[int] = None
    format: Optional[str] = None

    def get_object_cnt(self, definitions):
        result = 0
        if self.type:
            if self.type == "object":
                result += 1
        if self.items:
            result += self.items.get_object_cnt(definitions)
        if self.ref:
            definition_name = extract_definition_name(self.ref)
            result += definitions[definition_name].get_object_cnt(definitions)
        return result

    def get_data(self, field_name, definitions, object_name, parent_field_name):
        if self.items:
            property =  self.items.get_data(field_name, definitions, object_name, parent_field_name)
            if property:
                return property
        if self.ref:
            definition_name = extract_definition_name(self.ref)
            data = definitions[definition_name].get_data(field_name, definitions, object_name, parent_field_name)
            if data:
                return data
        return None




    def get_rules(self, definitions, object_name, field_name, rule_collection_flag = True):
        result = {}
        result["info"] = self
        result["rules"] = RuleSet()
        result["object_name"] = object_name
        result["field_name"] = field_name

        if rule_collection_flag:
            if self.maxLength is not None:
                causes = [Cause(name="jsonSchema.property.maxLength", sentence=str(self.maxLength))]
                result["rules"].add(Rule.create_max_length(self.maxLength, causes))
            if self.minLength is not None:
                causes = [Cause(name="jsonSchema.property.minLength", sentence=str(self.minLength))]
                result["rules"].add(Rule.create_min_length(self.minLength, causes))
            if self.minItems is not None:
                causes = [Cause(name="jsonSchema.property.minItems", sentence=str(self.minItems))]
                result["rules"].add(Rule.create_min_items(self.minItems, causes))
            if self.maxItems is not None:
                causes = [Cause(name="jsonSchema.property.maxItems", sentence=str(self.maxItems))]
                result["rules"].add(Rule.create_max_items(self.maxItems, causes))
            if self.enum:
                causes = [Cause(name="jsonSchema.property.enum", sentence=",".join(self.enum))]
                result["rules"].add(Rule.create_enum(self.enum, causes))
            if self.minimum is not None:
                causes = [Cause(name="jsonSchema.property.minimum", sentence=str(self.minimum))]
                result["rules"].add(Rule.create_minimum(self.minimum, causes))
            if self.maximum is not None:
                causes = [Cause(name="jsonSchema.property.maximum", sentence=str(self.maximum))]
                result["rules"].add(Rule.create_maximum(self.maximum, causes))
            if self.format:
                causes = [Cause(name="jsonSchema.property.format", sentence=str(self.format))]
                result["rules"].add(Rule.create_format(self.format, causes))
        if self.items:
            result["item"] = self.items.get_rules(
                definitions, object_name, field_name, rule_collection_flag
            )
        if self.ref:
            definition_name = extract_definition_name(self.ref)
            return definitions[definition_name].get_rules(definitions, object_name, definition_name, field_name, rule_collection_flag)
        if self.type:
            causes = [Cause(name="jsonSchema.property.type", sentence=self.type)]
            result["rules"].add(Rule.create_type(self.type, causes))
        return result


    def generate(self, name:str, rule_collect_entity_id_list, json_schema):
        print(f"key: {name}")
        if self.ref:
            ref = extract_definition_name(self.ref)
            return json_schema.definitions.get(ref).generate(ref, rule_collect_entity_id_list, json_schema)
        match self.type:
            case "string":
                get_rules_from_rule_collect_entity_id_list(name, rule_collect_entity_id_list)
                return self.string_generate(rule_collect_entity_id_list, json_schema)
            case "array":
                return self.array_generate(rule_collect_entity_id_list, json_schema)
        return f"nothing: {self.type}"

        return self.type
    def string_generate(self, rule_collect_entity_id_list, json_schema):
        return "string_gen"

    def array_generate(self, rule_collect_entity_id_list, json_schema):
        result = {}
        return "array_gen"

    @field_validator("description", mode="before")
    @classmethod
    def clean_description(cls, value: Optional[str]) -> Optional[str]:
        return value.replace("\r", "").replace("\n", " ").strip() if value else None


class DefinitionType(BaseModel):
    description: Optional[str] = None
    javaType: Optional[str] = None
    type: str
    properties: Optional[Dict[str, PropertyType]] = None
    required: Optional[List[str]] = None
    additionalProperties: Optional[bool] = None
    enum: Optional[List[str]] = None

    def get_object_cnt(self, definitions):
        result = 0
        if self.type:
            if self.type == "object":
                result += 1
        if self.properties:
            for key, property in self.properties.items():
                result += property.get_object_cnt(definitions)
        return result

    def get_data(self, field_name, definitions, object_name, parent_field_name = None):
        if self.properties:
            for key, property in self.properties.items():

                if key == field_name:
                    hit = False
                    if parent_field_name:
                        if object_name == parent_field_name:
                            hit = True
                    else:
                        hit = True
                    if hit:
                        if property.ref:
                            definition_name = extract_definition_name(property.ref)
                            return FixDataDTO(
                                object_name=object_name,
                                field_name=field_name,
                                value=definitions[definition_name]
                            )
                        return FixDataDTO(
                            object_name=object_name,
                            field_name=field_name,
                            value=property
                        )
                sub_property = property.get_data(field_name, definitions, key, parent_field_name)
                if sub_property:
                    return sub_property
        return None
    def get_rules(self, definitions, parent_name, object_name, field_name, rule_collection_flag = True):
        result = {}
        result["info"] = self
        result["rules"] = RuleSet()
        result["object_name"] = parent_name
        result["field_name"] = field_name
        if rule_collection_flag:
            if self.javaType:
                causes = [Cause(name="jsonSchema.definition.javaType", sentence=self.javaType)]
                result["rules"].add(Rule.create_java_type(self.javaType, causes))
            if self.enum:
                causes = [Cause(name="jsonSchema.definition.enum", sentence=",".join(self.enum))]
                result["rules"].add(Rule.create_enum(self.enum, causes))
        if self.type:
            causes = [Cause(name="jsonSchema.definition.type", sentence=self.type)]
            result["rules"].add(Rule.create_type(self.type, causes))
        if self.properties:
            result["properties"] = {}
            for key, property in self.properties.items():
                result["properties"][key] = property.get_rules(definitions, object_name, key, rule_collection_flag)
                if rule_collection_flag:
                    if self.required and key in self.required:
                        causes = [Cause(name="jsonSchema.definition.required", sentence=",".join(self.required))]
                        result["properties"][key]["rules"].add(Rule.create_required(causes))


        return result


    def generate(self, name:str, rule_collect_entity_id_list, json_schema):
        result = {}
        if self.properties is not None:
            for key, property in self.properties.items():
                result[key] = property.generate(name + "." + key, rule_collect_entity_id_list, json_schema)
        if self.enum is not None:
            return self.enum_string_generate(rule_collect_entity_id_list, json_schema)

        return result
    def enum_string_generate(self, rule_collect_entity_id_list, json_schema):
        return "enum_string_gen"

    @field_validator("description", mode="before")
    @classmethod
    def clean_description(cls, value: Optional[str]) -> Optional[str]:
        return value.replace("\r", "").replace("\n", " ").strip() if value else None

class FixDataDTO(BaseModel):
    object_name: Optional[str] = None
    field_name: Optional[str] = None
    value: Optional[Any] = None

class JsonSchema(BaseModel):
    schema: str = Field(..., alias="$schema")
    id: str = Field(..., alias="$id")
    comment: Optional[str] = None
    definitions: Dict[str, DefinitionType]
    properties: Dict[str, PropertyType]
    required: Optional[List[str]] = None
    additionalProperties: Optional[bool] = None

    def get_data(self, field_name, parent_field_name = None):
        for key, property in self.properties.items():
            if key == field_name:
                if property.ref:
                    definition_name = extract_definition_name(property.ref)
                    definition = self.definitions[definition_name]
                    return FixDataDTO(
                        object_name=self.id.split(":")[-1],
                        field_name = field_name,
                        value=definition
                    )
                return FixDataDTO(
                    object_name=self.id.split(":")[-1],
                    field_name=field_name,
                    value=property
                )
            sub_property = property.get_data(field_name, self.definitions, key, parent_field_name)
            if sub_property:
                return sub_property
        return None

    def get_object_cnt(self):
        result = 1
        for key, property in self.properties.items():
            result += property.get_object_cnt(self.definitions)
        return result



    def collect_rules(self, rule_collection_flag = True):
        result = {}
        result["properties"] = {}
        result["rules"] = RuleSet()
        object_name =self.id.split(":")[-1]
        for key, property in self.properties.items():
            result["properties"][key] = property.get_rules(self.definitions, object_name, key, rule_collection_flag)
            if rule_collection_flag:
                if self.required and key in self.required:
                    causes = [Cause(name="jsonSchema.required", sentence=",".join(self.required))]
                    result["properties"][key]["rules"].add(Rule.create_required(causes))

        return result




def get_json_schemas(directory_path)-> Dict[str, JsonSchema]:
    json_schemas: Dict[str, JsonSchema] = {}
    for file_path in Path(directory_path).rglob("*.json"):
        try:
            with open(file_path, "r", encoding="utf-8") as file:
                json_data = json.load(file)
                schema = JsonSchema(**json_data)
                json_schemas[schema.id.split(":")[-1]] = schema
        except (json.JSONDecodeError, IOError) as e:
            print(f"file {file_path} : {e}")
    return json_schemas

def get_json_schema_text(directory_path, message_name):
    try:
        with open(directory_path + f"/{message_name}.json", "r", encoding="utf-8") as file:
            return json.load(file)
    except (json.JSONDecodeError, IOError) as e:
        print(e)
        pass
    return None


def get_description_and_properties_from_schemas(object, json_schemas:Dict[str, JsonSchema]) -> (str, Dict[str, PropertyType]):
    from parser_modules.specification.message import Message
    from parser_modules.specification.data_type import DataType
    if isinstance(object, Message):
        message = json_schemas.get(object.name)
        if message is not None:
            return ("", message.properties)
        return "", None
    elif isinstance(object, DataType):
        match_json_schemas: List[JsonSchema] = [
            schema for schema in json_schemas.values()
            if hasattr(schema, "definitions") and object.name in schema.definitions
        ]

        if diff_check(object.name, match_json_schemas):
            if match_json_schemas:
                data_type = match_json_schemas[0].definitions[object.name]
                return (data_type.description, data_type.properties)
            else:
                print(f"unMatch {object.name}")
        return "", None





def diff_check(object_name: str, match_json_schemas: List[JsonSchema]) -> bool:
    definitions_list: List[Dict] = []

    for schema in match_json_schemas:
        if object_name in schema.definitions:
            definitions_list.append(schema.definitions[object_name].dict())
        else:
            return False

    if len(definitions_list) < 2:
        return True

    base_def = definitions_list[0]
    for idx, other_def in enumerate(definitions_list[1:], start=1):
        diff = DeepDiff(base_def, other_def, ignore_order=True)
        if diff:
            print(f"Definition  (Schema {idx}):")
            print(diff)
            return False
    return True

def extract_definition_name(ref: str) -> str:
    match = re.search(r"#/definitions/([\w\d_]+)", ref)
    return match.group(1) if match else ""

def get_rules_from_rule_collect_entity_id_list(name:str, rule_collect_entity_id_list):
    rule_collect_detail_entity_list = session.query(RuleCollectDetailEntity).filter(RuleCollectDetailEntity.rule_collect_id.in_(rule_collect_entity_id_list), RuleCollectDetailEntity.name == name).all()
    return  Rule(rule_collect_detail_entity_list)
    