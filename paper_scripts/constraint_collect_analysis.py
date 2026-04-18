from parser_modules.json.json_schema import get_json_schemas, JsonSchema, PropertyType, \
    get_description_and_properties_from_schemas
from parser_modules.parser import Parser
from constants.version_config import version201
from storage.entity.rule_collect_detail_entity import RuleCollectDetailEntity
import re
print("Hello world!")

from storage.entity.base_entity import session

def constraint_report(rule_collect_id:int):

    constraint_sum = 0
    rule_sum = 0
    condition_sum = 0
    rule_collect_detail_list:list[RuleCollectDetailEntity] = session.query(RuleCollectDetailEntity).filter_by(rule_collect_id=rule_collect_id)
    constraint_pair_set = set()
    for rule_collect_detail in rule_collect_detail_list:
        for rule in rule_collect_detail.rule_list:
            rule_sum = rule_sum + 1
            for constraint in rule.constraint_list:
                constraint_sum = constraint_sum + 1
                constraint_pair_set.add((constraint.attribute_entity.value, constraint.operator_entity.value))

            for condition in rule.condition_list:
                condition_sum = condition_sum + 1

    print(f"constraint_sum: {constraint_sum}")
    print(f"rule_sum: {rule_sum}")
    print(f"condition_sum: {condition_sum}")

    print(f"combination_sum: {constraint_pair_set.__len__()}")
    print(constraint_pair_set)

def get_min_max_items(card:str):
    list = card.split("..")
    return list[0], list[1]

def get_min_max_length(field_type:str):
    match = re.search(r'\[(\d+)\.\.(\d+)\]', field_type)
    if match:
        return int(match.group(1)), int(match.group(2))
    return None, None

def is_array_card(card:str):
    return card.strip()[-1] != "1"

def array_min_items_check(property:PropertyType, card):
    minItems, maxItems = get_min_max_items(card)
    return str(property.minItems) == str(minItems)

def array_max_items_check(property:PropertyType, card):
    minItems, maxItems = get_min_max_items(card)
    return str(property.maxItems) == str(maxItems) or  (property.maxItems is None and maxItems == "*")

def max_length_check(property:PropertyType, card, type):
    minLength, maxLength = get_min_max_length(type)
    target = property.maxLength
    if is_array_card(card):
        if property.items.maxLength:
            target = property.items.maxLength
    return str(target) == str(maxLength) or (not target and maxLength is None)

def min_length_check(property:PropertyType, card, type):
    minLength, maxLength = get_min_max_length(type)
    target = property.minLength
    if is_array_card(card):
        if property.items.minLength:
            target = property.items.minLength
    return str(target) == str(minLength) or (not target and str(minLength) == "0")

def diff_check():
    global config, json_schemas, parser
    diff_min_item_list = []
    diff_max_item_list = []
    diff_min_length_list = []
    diff_max_length_list = []
    for message in parser.messages:
        schema: JsonSchema = json_schemas.get(message.name)
        for field in message.fields:
            if field.name == "customData":
                continue
            property: PropertyType = schema.properties.get(field.name)
            if is_array_card(field.card):
                if array_min_items_check(property, field.card) is False:
                    diff_min_item_list.append(f"{message.name}.{field.name} ")
                if array_max_items_check(property, field.card) is False:
                    diff_max_item_list.append(f"{message.name}.{field.name} ")
            if max_length_check(property, field.card, field.type) is False:
                diff_max_length_list.append(f"{message.name}.{field.name}")
            if min_length_check(property, field.card, field.type) is False:
                diff_min_length_list.append(f"{message.name}.{field.name} ")
    for data_type in parser.data_types:
        description, properties = get_description_and_properties_from_schemas(data_type, json_schemas)
        for field in data_type.fields:
            if field.name == "customData":
                continue
            property: PropertyType = properties.get(field.name)
            if is_array_card(field.card):
                if array_min_items_check(property, field.card) is False:
                    diff_min_item_list.append(f"{data_type.name}.{field.name} ")
                if array_max_items_check(property, field.card) is False:
                    diff_max_item_list.append(f"{data_type.name}.{field.name} ")
            if max_length_check(property, field.card, field.type) is False:
                diff_max_length_list.append(f"{data_type.name}.{field.name}")
            if min_length_check(property, field.card, field.type) is False:
                diff_min_length_list.append(f"{data_type.name}.{field.name} ")
    config = version201
    json_schemas = get_json_schemas(config.json_schema_folder_path)
    parser = Parser(config)
    print(f"diff_min_item_list length: {len(diff_min_item_list)}")
    print(f"diff_max_item_list length: {len(diff_max_item_list)}")
    print(f"diff_min_length_list length: {len(diff_min_length_list)}")
    print(f"diff_max_length_list length: {len(diff_max_length_list)}")
    print(diff_min_length_list)
    print(diff_max_length_list)

config = version201
json_schemas = get_json_schemas(config.json_schema_folder_path)
parser = Parser(config)

# diff_check()
constraint_report(64)