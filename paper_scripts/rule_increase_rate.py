from sqlalchemy import and_

from parser_modules.parser import Parser
from rule_collector_modules.rule_set import RuleSet
from constants.version_config import version201
from storage.entity.base_entity import Base, session
from storage.entity.rule_collect_detail_entity import RuleCollectDetailEntity
from storage.db_engine import engine

from collections import defaultdict
from storage.loader.model_loader import ModelLoader
import matplotlib.pyplot as plt
loader = ModelLoader("storage.entity")
loader.load_models()

config = version201
parser = Parser(config)

Base.metadata.create_all(engine)
rule_collect_id_list = list(range(87,97))
rule_collect_id_list = list(range(164,174))

field_cnt = len(parser.primitive_data_types)
for message in parser.messages:
    field_cnt += len(message.fields)
for data_type in parser.data_types:
    field_cnt += len(data_type.fields)

rule_collect_detail_list = session.query(RuleCollectDetailEntity).filter(
    and_(
        RuleCollectDetailEntity.rule_collect_id.in_(rule_collect_id_list)
    )
).all()

group_dict = defaultdict(lambda: defaultdict(lambda: defaultdict(set)))

for detail in rule_collect_detail_list:
    for rule in detail.get_valid_rule_list():
        group_dict[detail.object_name][detail.name][detail.rule_collect_id].add(rule)

rule_count_per_collect_id = defaultdict(int)
unique_detail_keys = set()
global_rule_set_map = defaultdict(RuleSet)

total_rule_count = 0

for rule_collect_id in rule_collect_id_list:
    new_rule_count = 0

    for object_name, detail_map in group_dict.items():
        for detail_name, rule_collect_map in detail_map.items():
            key = (object_name, detail_name)
            unique_detail_keys.add(key)

            if rule_collect_id not in rule_collect_map:
                continue

            rule_list = rule_collect_map[rule_collect_id]
            rule_set = global_rule_set_map[key]

            for rule in rule_list:
                if rule_set.add(item=rule.to_dto(), rule_field_name=detail_name):
                    new_rule_count += 1

    total_rule_count += new_rule_count
    rule_count_per_collect_id[rule_collect_id] = total_rule_count

detail_key_count = len(unique_detail_keys)
iterations = list(range(1, len(rule_count_per_collect_id) + 1))
percentages = [(value / field_cnt) * 100 for value in rule_count_per_collect_id.values()]

plt.figure(figsize=(8, 5))
plt.plot(iterations, percentages, marker='o')

for value in percentages:
    print(value)

print("detail_key_count", detail_key_count)
print("field_cnt", field_cnt)
print("value", list(rule_count_per_collect_id.values())[-1])
plt.xlabel('Iteration Count')
plt.ylabel('Average Rules Collected per Field (%)')
plt.grid(True)
plt.xticks(iterations)
min_y = min(percentages)
max_y = max(percentages)
plt.ylim(min_y - 1, max_y + 1)
plt.show()