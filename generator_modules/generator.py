from typing import List
import sys
import traceback
from generator_modules.fix_value_container import FixValueContainer
from generator_modules.payload_context import PayloadContext
from generator_modules.payload_generator import PayloadGenerator
from parser_modules.json.json_schema import JsonSchema, PropertyType, DefinitionType
from parser_modules.parser import Parser
from rule_collector_modules.rule_set import RuleSet
from constants.version_config import Config
from rule_collector_modules.constraint_define import ConstraintDefine, ConstraintEnum
from dataset.scripts.descripitive_rule_result import DescriptiveRuleResult
from storage.entity.generate_entity import GenerateEntity
from storage.entity.generate_message_entity import GenerateMessageEntity
from storage.entity.generate_message_fail_entity import GenerateMessageFailEntity
from storage.entity.generate_rule_combination_entity import GenerateRuleCombinationEntity
from storage.entity.generate_rule_entity import GenerateRuleEntity
from storage.entity.test_entity import TestEntity
from exception.insufficient_data_exception import InsufficientDataException
from exception.uncreatable_value_exception import UncreatableValueException

from generator_modules.manual_rule import ManualRule, get_manual_rule_list

sys.set_int_max_str_digits(12000)

def rule_serializer(obj):
    if isinstance(obj, RuleSet):
        return list(obj)
    elif hasattr(obj, "__dict__"):
        return obj.__dict__
    return str(obj)
class GenerateTriggerMessageDTO:
    def __init__(self, generate_message_entity, request_id_log_entity):
        self.generate_message_entity = generate_message_entity
        self.request_id_log_entity = request_id_log_entity

class Generator:
    STAND_BY = "STAND_BY"
    EMPTY_VALUE = "EMPTY_VALUE"
    DEFAULT_MIN_LENGTH = 0
    DEFAULT_MAX_LENGTH = 12000
    DEFAULT_MIN_SIZE = 0
    DEFAULT_MAX_SIZE = 20
    MAX_SIZE_APPEND = 5
    INTEGER_MIN_SIZE = -sys.maxsize - 1
    INTEGER_MAX_SIZE = sys.maxsize
    def __init__(self, config:Config, message_name:str, json_schema: JsonSchema, parser:Parser, fix_value_container:FixValueContainer, test_controller_manager, test_entity_id, session, gen_cnt = 1, rule_collection_flag = True, descriptive_rule_result:DescriptiveRuleResult = None):
        self.fix_value_container =fix_value_container
        self.message_name = message_name
        self.json_schema = json_schema
        self.rule_collection_flag = rule_collection_flag
        self.descriptive_rule_result = descriptive_rule_result
        self.parser = parser
        self.config = config
        self.gen_cnt = gen_cnt
        self.manual_rule_list:List[ManualRule] = get_manual_rule_list(config.version)
        self.test_controller_manager = test_controller_manager
        self.session = session
        self.test_entity = session.query(TestEntity).get(test_entity_id)
        self.rules = self.collect_rules()
        self.generate_entity = self.create_generate_entity(config)
        session.commit()
        self.rules = self.extract_rules(self.rules)
        session.commit()
        self.combinations = self.generate_combinations()
        print("combination length", len(self.combinations))


    def get_all_true_combo(self):
        all_true_combo = [c for c in self.combinations if all(c.values())]
        if not all_true_combo:
            return None
        return all_true_combo[0]

    def generate_true_message_entity(self, context:PayloadContext = None):
        all_true_combo= self.get_all_true_combo()
        result = []
        self.gen_cnt = 1
        self.generate_call_message_list(combination=all_true_combo, result = result, context = context)
        if len(result) > 0:
            return result[0]
        return None

    def generate_message_entity(self, combination, context:PayloadContext = None):
        result = []
        self.gen_cnt = 1
        self.generate_call_message_list(combination, result, context)
        if len(result) > 0:
            return result[0]
        return None

    def generate_true_response_payload(self):
        all_true_combo = self.get_all_true_combo()
        generate_rule_combination_entity = GenerateRuleCombinationEntity(
            generate_entity=self.generate_entity,
            combination=all_true_combo
        )
        self.session.add(generate_rule_combination_entity)
        self.session.commit()

        payload_generator = PayloadGenerator(
            message_name=self.message_name,
            rules=self.rules,
            generate_rule_combination_entity=generate_rule_combination_entity,
            fix_value_container=self.fix_value_container,
            parser=self.parser,
            test_controller_manager=self.test_controller_manager,
            session=self.session
        )
        return str(payload_generator.create())

    def generate(self, context:PayloadContext = None):
        result = []
        for combination in self.combinations:
            self.generate_call_message_list(combination=combination, result=result, context=context)
        return result

    def generate_call_message_list(self, combination, result, context:PayloadContext = None):
        generate_rule_combination_entity = GenerateRuleCombinationEntity(
            generate_entity=self.generate_entity,
            combination=combination
        )
        self.session.add(generate_rule_combination_entity)
        self.session.commit()

        payload_generator = PayloadGenerator(
            message_name=self.message_name,
            rules=self.rules,
            generate_rule_combination_entity=generate_rule_combination_entity,
            fix_value_container=self.fix_value_container,
            parser=self.parser,
            test_controller_manager=self.test_controller_manager,
            session=self.session
        )
        for i in range(self.gen_cnt):
            try:
                message_payload = payload_generator.create(context=context)
                generate_message_entity = GenerateMessageEntity(
                    generate_rule_combination_entity=generate_rule_combination_entity,
                    message_type_id= 2 if self.message_name.endswith("Request") else 3,
                    action=self.message_name,
                    payload=str(message_payload),
                    test_entity=self.test_entity
                )
                self.session.add(generate_message_entity)
                self.session.flush()
                result.append(generate_message_entity)

            except InsufficientDataException as e:
                self.session.add(GenerateMessageFailEntity(
                    generate_rule_combination_entity=generate_rule_combination_entity,
                    exception="InsufficientDataException",
                    cause=str(e),
                    test_entity=self.test_entity
                ))
            except UncreatableValueException as e:
                self.session.add(GenerateMessageFailEntity(
                    generate_rule_combination_entity=generate_rule_combination_entity,
                    exception="UncreatableValueException",
                    cause=str(e),
                    test_entity=self.test_entity
                ))
            except Exception as e:
                print("[Exception]")
                self.session.add(GenerateMessageFailEntity(
                    generate_rule_combination_entity=generate_rule_combination_entity,
                    exception="Unknown",
                    cause=str(e),
                    test_entity=self.test_entity
                ))
                traceback.print_exc()
        self.session.commit()

    def generate_combinations(self):
        result = []

        base = {generate_rule_entity: True for generate_rule_entity in self.generate_entity.generate_rule_list}
        all_true = base.copy()
        result.append(all_true)
        for generate_rule_entity in self.generate_entity.generate_rule_list:
            temp = base.copy()
            temp[generate_rule_entity] = False
            result.append(temp)
        return result

    def extract_rules(self, data):
        if isinstance(data, dict):
            for key, value in data.items():
                if key == "rules":
                    if isinstance(value, RuleSet):
                        new_rules = RuleSet()
                        for rule in value:
                            copied_rule = rule.clone()
                            if new_rules.add(copied_rule):
                                generate_rule_entity = GenerateRuleEntity(
                                    generate_entity=self.generate_entity,
                                    rule=copied_rule,
                                    object_name=data["object_name"],
                                    field_name=data["field_name"] if "field_name" in data else None,
                                    session=self.session
                                )
                                self.session.add(generate_rule_entity)
                                self.generate_entity.generate_rule_list.append(generate_rule_entity)
                                self.session.commit()
                                copied_rule._generate_rule_entity = generate_rule_entity
                        data[key] = new_rules
                else:
                    data[key] = self.extract_rules(value)
        elif isinstance(data, list):
            for i in range(len(data)):
                data[i] = self.extract_rules(data[i])
        return data

    def check_rules(self,data):
        if isinstance(data, dict):
            for key, value in data.items():
                self.check_rules(value)
        elif isinstance(data, list):
            for item in data:
                self.check_rules(item)

    def get_combination_value_entity(self, generate_rule_combination_entity, rule):
        return next(
            (
                grcve for grcve in generate_rule_combination_entity.generate_rule_combination_value_entity_list
                if grcve.generate_rule_id == rule._generate_rule_entity.id
            ),
            None
        )

    def create_generate_entity(self, config):
        generate_entity = GenerateEntity(
            message_name=self.message_name,
            document_path=config.document_path,
            json_schema_folder_path=config.json_schema_folder_path
        )
        self.session.add(generate_entity)
        self.session.commit()
        return generate_entity

    def collect_rules(self):
        base_rules = self.json_schema.collect_rules(rule_collection_flag=self.rule_collection_flag)
        if not self.rule_collection_flag:
            return base_rules

        match_pdf_messages = [
            message for message in self.parser.messages
            if message.name == self.message_name
        ]

        def apply_rules(key, item):
            object_name = None
            if isinstance(item.get("info"), PropertyType):
                if item.get("item"):
                    apply_rules(key, item.get("item"))
            if isinstance(item.get("info"), DefinitionType):
                object_name = item.get("info").javaType + "Type" if item.get("info") else None
            if object_name:
                match_pdf_data_types = [
                    data_type for data_type in self.parser.data_types
                    if data_type.name == object_name
                ]

                if "properties" in item:
                    for sub_key, sub_item in item["properties"].items():
                        if self.descriptive_rule_result is not None:
                            descriptive_rule_list = self.descriptive_rule_result.get_rule_list(object_name = object_name, field_name=sub_key)
                            for rule in descriptive_rule_list:
                                constraint_enum = ConstraintDefine.getConstraintEnum(rule.constraint)
                                if "item" in item:
                                    match constraint_enum:
                                        case ConstraintEnum.MAX_LENGTH | ConstraintEnum.ENUM:
                                            sub_item["item"]["rules"].add(rule, rule_field_name=sub_key)
                                            continue
                                sub_item["rules"].add(rule, rule_field_name=sub_key)

                        if match_pdf_data_types:
                            for data_type in match_pdf_data_types:
                                for field in data_type.fields:
                                    if field.name == sub_key:
                                        match_primitive_datatypes_rule_list = self.get_match_primitive_datatypes_rule_list(field.type)
                                        if match_primitive_datatypes_rule_list:
                                            for match_rule in match_primitive_datatypes_rule_list:
                                                if "item" in sub_item:
                                                    sub_item["item"]["rules"].add(match_rule, rule_field_name=sub_key)
                                                else:
                                                    sub_item["rules"].add(match_rule, rule_field_name=sub_key)

                                        match_manual_rule_list = self.get_match_manual_rule_list(object_name, field.name)
                                        if match_manual_rule_list:
                                            for match_manual_rule in match_manual_rule_list:
                                                if "item" in sub_item:
                                                    sub_item["item"]["rules"].add(match_manual_rule.rule, rule_field_name=sub_key)
                                                else:
                                                    sub_item["rules"].add(match_manual_rule.rule, rule_field_name=sub_key)
                                        for field_rule in field.get_rule_list():
                                            if "item" in sub_item:
                                                constraint_enum = ConstraintDefine.getConstraintEnum(field_rule.constraint)
                                                match constraint_enum:
                                                    case ConstraintEnum.MAX_LENGTH|ConstraintEnum.ENUM:
                                                        sub_item["item"]["rules"].add(field_rule, rule_field_name=sub_key)
                                                        continue
                                            sub_item["rules"].add(field_rule, rule_field_name=sub_key)

                        apply_rules(sub_key, sub_item)


        for key, item in base_rules["properties"].items():
            if self.descriptive_rule_result is not None:
                descriptive_rule_list = self.descriptive_rule_result.get_rule_list(object_name=self.message_name, field_name=key)
                for rule in descriptive_rule_list:
                    constraint_enum = ConstraintDefine.getConstraintEnum(rule.constraint)
                    if "item" in item:
                        match constraint_enum:
                            case ConstraintEnum.MAX_LENGTH | ConstraintEnum.ENUM|ConstraintEnum.VALUE_FROM:
                                item["item"]["rules"].add(rule, rule_field_name=key)
                                continue
                    item["rules"].add(rule, rule_field_name=key)

            if match_pdf_messages:
                for message in match_pdf_messages:
                    for field in message.fields:
                        if field.name == key:
                            for field_rule in field.get_rule_list():
                                constraint_enum = ConstraintDefine.getConstraintEnum(field_rule.constraint)
                                if "item" in item:
                                    match constraint_enum:
                                        case ConstraintEnum.MAX_LENGTH|ConstraintEnum.ENUM|ConstraintEnum.VALUE_FROM:
                                            item["item"]["rules"].add(field_rule, rule_field_name=field.name)
                                            continue
                                item["rules"].add(field_rule)
                            match_primitive_datatypes_rule_list = self.get_match_primitive_datatypes_rule_list(field.type)
                            if match_primitive_datatypes_rule_list:
                                for match_rule in match_primitive_datatypes_rule_list:
                                    if "item" in item:
                                        item["item"]["rules"].add(match_rule, rule_field_name=field.name)
                                    else:
                                        item["rules"].add(match_rule, rule_field_name=field.name)
                            match_manual_rule_list = self.get_match_manual_rule_list(message.name, field.name)
                            if match_manual_rule_list:
                                for match_manual_rule in match_manual_rule_list:
                                    if "item" in item:
                                        item["item"]["rules"].add(match_manual_rule.rule, rule_field_name=field.name)
                                    else:
                                        item["rules"].add(match_manual_rule.rule, rule_field_name=field.name)
            apply_rules(key, item)
        return base_rules


    def get_match_primitive_datatypes_rule_list(self, field_type):
        if self.descriptive_rule_result:
            if "[" in field_type:
                return self.descriptive_rule_result.get_rule_list(object_name="PrimitiveDatatypes", field_name=field_type.split("[")[0])
            if "," in field_type:
                return self.descriptive_rule_result.get_rule_list(object_name="PrimitiveDatatypes", field_name=field_type.split(",")[0])
            return self.descriptive_rule_result.get_rule_list(object_name="PrimitiveDatatypes",field_name=field_type)
        return None

    def get_match_manual_rule_list(self, object_name, field_name):
        return list(filter(lambda manual_rule : manual_rule.object_name == object_name and manual_rule.field_name == field_name, self.manual_rule_list))
