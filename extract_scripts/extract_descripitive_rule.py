import os

from sqlalchemy import and_
from generator_modules.generator import rule_serializer
from parser_modules.json.json_schema import get_json_schemas
from rule_collector_modules.rule_set import RuleSet
from constants.version_config import version201, Config
from storage.entity.base_entity import Base, session
from storage.entity.rule_collect_detail_entity import RuleCollectDetailEntity
from storage.db_engine import engine
from typing import List
import json
from storage.loader.model_loader import ModelLoader

loader = ModelLoader("storage.entity")
loader.load_models()
Base.metadata.create_all(engine)
config:Config = version201
json_schemas = get_json_schemas(config.json_schema_folder_path)
dataset_dir = os.path.join(os.getcwd(), "dataset")
os.makedirs(dataset_dir, exist_ok=True)
output_path = os.path.join(dataset_dir, "descripitive_rule_result.json")

class ExtractDescripitiveRule:
    def __init__(self, rule_collect_id_list:List[int]):
        self.rule_collect_id_list = rule_collect_id_list


    def run(self):
        result = {}
        rule_collect_detail_list = session.query(RuleCollectDetailEntity).filter(
            and_(
                RuleCollectDetailEntity.rule_collect_id.in_(self.rule_collect_id_list),
            )
        ).all()

        for rule_collect_detail in rule_collect_detail_list:
            if rule_collect_detail.name not in result.keys():
                result[rule_collect_detail.name] = RuleSet()
            for rule_entity in rule_collect_detail.rule_list:
                rule = rule_entity.to_dto()
                rule = result[rule_collect_detail.name].get_equivalent_rule(rule)
                if rule_entity.is_active == True and rule_entity.is_valid:
                    result[rule_collect_detail.name].add(rule)

        with open(output_path, "w", encoding="utf-8") as f:

            json.dump(result, f, ensure_ascii=False, indent=2, default=rule_serializer)

manual_rule_verifier = ExtractDescripitiveRule(rule_collect_id_list = list(range(164,174)))
manual_rule_verifier.run()