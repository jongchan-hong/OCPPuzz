import os
import json
from pydantic import BaseModel, validator
from typing import List, Union, Optional, Dict
from dto.constraint_collect_dto import Rule

class DescriptiveRuleResult:
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    FILE_PATH = os.path.join(BASE_DIR, "descripitive_rule_result.json")

    def __init__(self):
        self.descriptive_rules: Dict[str, List[Rule]] = self.load()

    def load(self):
        with open(self.FILE_PATH, "r", encoding="utf-8") as f:
            raw_data = json.load(f)
        parsed_data: Dict[str, List[Rule]] = {}
        for key, rule_list in raw_data.items():
            parsed_data[key] = [Rule(**rule_dict) for rule_dict in rule_list]
        return parsed_data

    def get_rule_list(self, object_name, field_name):
        full_name = f"{object_name}.{field_name}"
        return self.descriptive_rules.get(full_name, [])

