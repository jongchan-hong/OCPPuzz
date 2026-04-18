from sqlalchemy import and_
from parser_modules.json.json_schema import get_json_schemas
from rule_collector_modules.rule_set import RuleSet
from constants.version_config import version201, Config
from parser_modules.parser import Parser
from rule_collector_modules.constraint_define import ConstraintDefine
from dataset.scripts.message_direction_result import MessageDirectionResult
from storage.entity.base_entity import Base, session
from storage.entity.rule_collect_detail_entity import RuleCollectDetailEntity
from storage.entity.gpt_rule_collect_log_entity import GPTRuleCollectLogEntity
from storage.db_engine import engine
import queue

from storage.loader.model_loader import ModelLoader
from constants.category_map import CONSTRAINT_CATEGORY_MAP

loader = ModelLoader("storage.entity")
loader.load_models()
Base.metadata.create_all(engine)
config:Config = version201
json_schemas = get_json_schemas(config.json_schema_folder_path)
parser = Parser(config)
message_direction_result = MessageDirectionResult()
target_request_detail_list = message_direction_result.get_target_request_detail_list()
rule_collect_id_list = list(range(164,174))
primitive_datatypes_rule_list = session.query(RuleCollectDetailEntity).filter(
    and_(
        RuleCollectDetailEntity.rule_collect_id.in_(rule_collect_id_list),
        RuleCollectDetailEntity.object_name == "PrimitiveDatatypes"
    )
).all()

def enqueue_data_type(type_name):
    if type_name not in processed_data_types:
        data_type_queue.put(type_name)
        processed_data_types.add(type_name)

def get_try_cnt(object_name):
    log_list = session.query(GPTRuleCollectLogEntity).filter(
        GPTRuleCollectLogEntity.rule_collect_id.in_(rule_collect_id_list),
        GPTRuleCollectLogEntity.object_name == object_name,
        GPTRuleCollectLogEntity.response != None
    ).all()
    return len(log_list)

def get_total_rule_cnt(object_name):
    rule_collect_detail_list = session.query(RuleCollectDetailEntity).filter(
        and_(
            RuleCollectDetailEntity.rule_collect_id.in_(rule_collect_id_list),
            RuleCollectDetailEntity.object_name == object_name
        )
    ).all()
    return len(rule_collect_detail_list)

def get_unique_rule_cnt(object_name):
    rule_collect_detail_list = session.query(RuleCollectDetailEntity).filter(
        and_(
            RuleCollectDetailEntity.rule_collect_id.in_(rule_collect_id_list),
            RuleCollectDetailEntity.object_name == object_name
        )
    ).all()
    field_rule_set_dict = {}
    not_field_rule_set_dict = {}
    unique_rule_cnt = 0
    filtered_out_rule_cnt_dict = {
        "DataType": 0,
        "Presence": 0,
        "Content":0,
        "Size": 0,
    }
    unique_rule_cnt_dict = {
        "DataType": 0,
        "Presence": 0,
        "Content":0,
        "Size": 0,
    }
    for rule_collect_detail in rule_collect_detail_list:
        key = rule_collect_detail.name
        if key not in field_rule_set_dict:
            field_rule_set_dict[key] = RuleSet()
            not_field_rule_set_dict[key] = set()
        for rule_entity in rule_collect_detail.rule_list:
            if rule_entity.is_active == False and rule_entity.is_valid == False:
                # print(f"id: {rule_entity.id} / {object_name} / {key} / valid: {rule_entity.is_valid}")
                # print(rule_entity.to_dto())
                constraint_enum = ConstraintDefine.getConstraintEnum(rule_entity.to_dto().constraint)
                if constraint_enum is None:
                    continue
                not_field_rule_set_dict[key].add(constraint_enum)
                continue

            field_rule_set_dict[key].add(rule_entity.to_dto())


    for key, field_rule_set in field_rule_set_dict.items():
        for field_rule in field_rule_set:
            result = CONSTRAINT_CATEGORY_MAP.get(ConstraintDefine.getConstraintEnum(field_rule.constraint))
            if result is None:
                print(ConstraintDefine.getConstraintEnum(field_rule.constraint))
                exit()
            if unique_rule_cnt_dict[result] is None:
                print(field_rule.constraint)
                exit()
            unique_rule_cnt_dict[result] += 1

    for key, constraint_enum_set in not_field_rule_set_dict.items():
        for constraint_enum in constraint_enum_set:
            result = CONSTRAINT_CATEGORY_MAP.get(constraint_enum)
            filtered_out_rule_cnt_dict[result] += 1

    return unique_rule_cnt_dict, filtered_out_rule_cnt_dict

def get_json_rule_cnt(message_name):
    json_schema = json_schemas.get(message_name)
    base_rules = json_schema.collect_rules()

    return count_all_rules_recursively(base_rules)

def get_object_cnt(message_name):
    json_schema = json_schemas.get(message_name)
    return json_schema.get_object_cnt()

def count_all_rules_recursively(item: dict):
    total = 0
    data_type_rule_cnt = 0
    presence_rule_cnt = 0
    content_rule_cnt = 0
    size_rule_cnt = 0

    if not isinstance(item, dict):
        return 0, 0, 0, 0
    for key, value in item.items():
        if key == "rules":
            for rule in value:
                result = CONSTRAINT_CATEGORY_MAP.get(ConstraintDefine.getConstraintEnum(rule.constraint))
                match result:
                    case "DataType":
                        data_type_rule_cnt += 1
                    case "Presence":
                        presence_rule_cnt += 1
                    case "Content":
                        content_rule_cnt += 1
                    case "Size":
                        size_rule_cnt += 1
        elif isinstance(value, dict):
            dict_data_type_rule_cnt, dict_presence_rule_cnt, dict_content_rule_cnt, dict_size_rule_cnt = count_all_rules_recursively(value)
            data_type_rule_cnt += dict_data_type_rule_cnt
            presence_rule_cnt += dict_presence_rule_cnt
            content_rule_cnt += dict_content_rule_cnt
            size_rule_cnt += dict_size_rule_cnt
        elif isinstance(value, list):
            for inner_value in value:
                list_data_type_rule_cnt, list_presence_rule_cnt, list_content_rule_cnt, list_size_rule_cnt = count_all_rules_recursively(
                    inner_value)
                data_type_rule_cnt += list_data_type_rule_cnt
                presence_rule_cnt += list_presence_rule_cnt
                content_rule_cnt += list_content_rule_cnt
                size_rule_cnt += list_size_rule_cnt
    return data_type_rule_cnt, presence_rule_cnt, content_rule_cnt, size_rule_cnt



def count_primitive_data_type_cnt(field_type):
    return len(get_primitive_data_type_rule_set(field_type))

def get_primitive_data_type_rule_set(field_type):
    type = field_type.split("[")[0]
    rule_set = RuleSet()
    for primitive_datatypes_rule in primitive_datatypes_rule_list:
        key = primitive_datatypes_rule.name.split(".")[-1]
        if key == type:
            for rule in primitive_datatypes_rule.get_active_rule_list():
                rule_set.add(rule.to_dto())
    return rule_set

result= {}
for message in parser.messages:
    if message.name in target_request_detail_list:
        # generator = Generator(
        #     config=config,
        #     message_name=message.name,
        #     json_schema=json_schemas.get(message.name),
        #     rule_collect_id_list=rule_collect_id_list,
        #     parser=parser,
        #     fix_value_container=FixValueContainer()
        # )

        result[message.name]= {}
        result[message.name]["collect_try_cnt"] = 0
        result[message.name]["valid_unique_rules_cnt"] = 0
        result[message.name]["filtered_unique_rules_cnt"] = 0
        result[message.name]["affect_primitive_collect_rule_cnt"] = 0
        result[message.name]["collect_structural_rules"] = {}
        result[message.name]["collect_structural_rules"]["DataType"],\
            result[message.name]["collect_structural_rules"]["Presence"],\
            result[message.name]["collect_structural_rules"]["Content"],\
            result[message.name]["collect_structural_rules"]["Size"] = get_json_rule_cnt(message.name)
        result[message.name]["collect_structural_rules"]["Extracted"] = result[message.name]["collect_structural_rules"]["DataType"] + result[message.name]["collect_structural_rules"]["Presence"] + result[message.name]["collect_structural_rules"]["Content"]+ result[message.name]["collect_structural_rules"]["Size"]
        result[message.name]["valid"] = {
            "DataType": 0,
            "Presence": 0,
            "Content":0,
            "Size": 0,
        }
        result[message.name]["filtered"] = {
            "DataType": 0,
            "Presence": 0,
            "Content":0,
            "Size": 0,
        }

        data_type_queue = queue.Queue()
        processed_data_types = set()

        result[message.name]["collect_try_cnt"] += get_try_cnt(message.name)
        filtered_unique_rule_cnt_dict, filtered_out_unique_rule_cnt_dict = get_unique_rule_cnt(message.name)


        for key, cnt in filtered_unique_rule_cnt_dict.items():
            result[message.name]["valid"][key] += cnt

        for key, cnt in filtered_out_unique_rule_cnt_dict.items():
            result[message.name]["filtered"][key] += cnt


        for field in message.fields:
            if not field.type.endswith("EnumType") and field.type.endswith("Type"):
                enqueue_data_type(field.type)
            else:
                primitive_rule_set = get_primitive_data_type_rule_set(field.type)
                for primitive_type in primitive_rule_set:
                    valid_key = CONSTRAINT_CATEGORY_MAP.get(ConstraintDefine.getConstraintEnum(primitive_type.constraint))
                    result[message.name]["valid"][valid_key] += 1

                result[message.name]["affect_primitive_collect_rule_cnt"] += count_primitive_data_type_cnt(field.type)

        while data_type_queue.empty() == False:
            name = data_type_queue.get()
            result[message.name]["collect_try_cnt"] += get_try_cnt(name)
            filtered_unique_rule_cnt_dict, filtered_out_unique_rule_cnt_dict = get_unique_rule_cnt(name)

            for key, cnt in filtered_unique_rule_cnt_dict.items():
                result[message.name]["valid"][key] += cnt

            for key, cnt in filtered_out_unique_rule_cnt_dict.items():
                result[message.name]["filtered"][key] += cnt
            for data_type in parser.data_types:
                if data_type.name == name:
                    for field in data_type.fields:
                        if not field.type.endswith("EnumType") and field.type.endswith("Type"):
                            enqueue_data_type(field.type)
                        else:
                            primitive_rule_set = get_primitive_data_type_rule_set(field.type)
                            for primitive_type in primitive_rule_set:
                                valid_key = CONSTRAINT_CATEGORY_MAP.get(ConstraintDefine.getConstraintEnum(primitive_type.constraint))
                                result[message.name]["valid"][valid_key] += 1
                            result[message.name]["affect_primitive_collect_rule_cnt"] += count_primitive_data_type_cnt(
                                field.type)

        # add custom data * 2
        # message object 1 c2
        #
        result[message.name]["object_cnt"] = get_object_cnt(message.name)

from decimal import Decimal, ROUND_HALF_UP
# Collect Result Table Value
def _fmt_num(x):
    d = Decimal(str(x))
    if d == d.to_integral_value():
        return str(int(d))
    frac_places = max(0, -d.normalize().as_tuple().exponent)
    if frac_places > 2:
        d = d.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    s = format(d.normalize(), 'f')
    return s

def _fmt_pct(v, t):
    if t == 0:
        return "0.0\\%"
    pct = (Decimal(str(v)) / Decimal(str(t))) * Decimal('100')
    pct = pct.quantize(Decimal('0.1'), rounding=ROUND_HALF_UP)  # 1 decimal place
    return f"{pct}\\%"

def fmt(v, f):  # per-cell: valid/failed -> valid/total (xx.x\%)
    t = v + f
    if t == 0:
        return f"0"
    return f"{_fmt_num(v)}/{_fmt_num(t)} ({_fmt_pct(v, t)})"
is_first = True
for key, item in result.items():
    if not is_first:
        print(f"\\hline")
    else:
        is_first = False
    print(key.rsplit("Request", 1)[0], end=" & ")
    print(item["object_cnt"], end=" & ")
    print(f"{item["collect_structural_rules"]['DataType']}", end=" & ")
    print(f"{item["collect_structural_rules"]['Presence']}", end=" & ")
    print(f"{item["collect_structural_rules"]['Content']}", end=" & ")
    print(f"{item["collect_structural_rules"]['Size']}", end=" & ")
    print(f"{item["collect_structural_rules"]['Extracted']}", end=" & ")
    valid_sum = 0
    filtered_sum = 0
    for item_key, item_value in item["valid"].items():
        if item_key == "DataType":
            continue
        valid_sum += item_value
        filtered_sum += item["filtered"][item_key]
        print(fmt(item_value, item["filtered"][item_key]), end=" & ")
    print(f"{fmt(valid_sum, filtered_sum)} \\\\")



total_messages = len(result)
sum_object = sum(item["object_cnt"] for item in result.values())
sum_structural_data_type_rules_cnt = sum(item["collect_structural_rules"]['DataType'] for item in result.values())
sum_structural_presence_rules_cnt = sum(item["collect_structural_rules"]['Presence'] for item in result.values())
sum_structural_content_rules_cnt = sum(item["collect_structural_rules"]['Content'] for item in result.values())
sum_structural_size_rules_cnt = sum(item["collect_structural_rules"]['Size'] for item in result.values())
sum_structural_extracted_rules_cnt = sum(item["collect_structural_rules"]['Extracted'] for item in result.values())
sum_data_type_valid_rules = sum(item["valid"]["DataType"] for item in result.values())
sum_data_type_filtered_rules = sum(item["filtered"]["DataType"] for item in result.values())
sum_presence_valid_rules = sum(item["valid"]["Presence"] for item in result.values())
sum_presence_filtered_rules = sum(item["filtered"]["Presence"] for item in result.values())
sum_content_valid_rules = sum(item["valid"]["Content"] for item in result.values())
sum_content_filtered_rules = sum(item["filtered"]["Content"] for item in result.values())
sum_size_valid_rules = sum(item["valid"]["Size"] for item in result.values())
sum_size_filtered_rules = sum(item["filtered"]["Size"] for item in result.values())

sum_try = sum(item["collect_try_cnt"] for item in result.values())
sum_invalid = sum_data_type_filtered_rules + sum_presence_filtered_rules + sum_content_filtered_rules + sum_size_filtered_rules
sum_valid = sum_data_type_valid_rules + sum_presence_valid_rules + sum_content_valid_rules + sum_size_valid_rules

def get_avg(total_count):
    result = round(total_count / total_messages, 2)
    if result == 0:
        return 0
    return result

avg_object = round(sum_object / total_messages, 2)
avg_structural_data_type_rules_cnt = round(sum_structural_data_type_rules_cnt / total_messages, 2)
avg_structural_presence_rules_cnt = round(sum_structural_presence_rules_cnt / total_messages, 2)
avg_structural_content_rules_cnt = round(sum_structural_content_rules_cnt / total_messages, 2)
avg_structural_size_rules_cnt = round(sum_structural_size_rules_cnt / total_messages, 2)
avg_structural_extracted_rules_cnt = round(sum_structural_size_rules_cnt / total_messages, 2)
avg_try = round(sum_try / total_messages, 2)
avg_invalid = round(sum_invalid / total_messages, 2)
avg_valid = round(sum_valid / total_messages, 2)
avg_rule = round((sum_valid + sum_invalid) / total_messages, 2)
print()
def bf(x):
    return rf"\textbf{{{x}}}"


print(rf"\midrule")
print(
    f"{bf('Sum')} & {sum_object} & {sum_structural_data_type_rules_cnt} & {sum_structural_presence_rules_cnt} & {sum_structural_content_rules_cnt} & {sum_structural_size_rules_cnt} & "
    f"{bf(sum_structural_extracted_rules_cnt)} & "
    # f"{fmt(sum_data_type_valid_rules, sum_data_type_filtered_rules)} & "
    f"{fmt(sum_presence_valid_rules, sum_presence_filtered_rules)} & "
    f"{fmt(sum_content_valid_rules, sum_content_filtered_rules)} & "
    f"{fmt(sum_size_valid_rules, sum_size_filtered_rules)} & "
    f"{bf(f'{fmt(sum_valid, sum_invalid)}')} \\\\"
)
print("\\hline")
print(
    f"{bf('Average')} & {get_avg(sum_object)} & "
    f"{get_avg(sum_structural_data_type_rules_cnt)}  & "
    f"{get_avg(sum_structural_presence_rules_cnt)}  & "
    f"{get_avg(sum_structural_content_rules_cnt)}  & "
    f"{get_avg(sum_structural_size_rules_cnt)}  & "
    f"{bf(get_avg(sum_structural_extracted_rules_cnt))}  & "
    # f"{fmt(get_avg(sum_data_type_valid_rules), get_avg(sum_data_type_filtered_rules))} & "
    f"{fmt(get_avg(sum_presence_valid_rules), get_avg(sum_presence_filtered_rules))} & "
    f"{fmt(get_avg(sum_content_valid_rules), get_avg(sum_content_filtered_rules))} & "
    f"{fmt(get_avg(sum_size_valid_rules), get_avg(sum_size_filtered_rules))} & "
    f"{bf(f'{fmt(get_avg(sum_valid), get_avg(sum_invalid))}')} \\\\"
)
# print(f"Average & {avg_object} & {avg_structural_rules_cnt}  & {avg_rule} & {avg_invalid} & {avg_valid} \\\\")