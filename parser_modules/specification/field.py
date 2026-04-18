from typing import List
from parser_modules.specification.enum_type import EnumMember
from dto.constraint_collect_dto import Rule, Cause
import re

class Field:
    def __init__(self, row: List[str]):
        self.name = row[0].replace("\n", "")
        self.type = row[1].replace("\n", "")
        self.card = row[2].replace("\n", "")
        self.description = row[3].replace("\n", " ")
        self.min_length = self.get_min_length()
        self.max_length = self.get_max_length()
        self.max_val = self.get_max_val()
        self.min_val = self.get_min_val()
        if self.card:
            min_max_size = self.card.split("..")
            self.min_size = min_max_size[0]
            self.max_size = min_max_size[1]

    def get_information(self, parser):
        result = {}
        result["name"] = self.name
        result["field_description"] = self.description
        if self.type.endswith("EnumType"):
            enumerations = list(filter(lambda enum_type: enum_type.name == self.type, parser.enumerations))
            if len(enumerations) > 0:
                enum_type:EnumMember = enumerations[0]
                if enum_type:
                    result["reference"] = enum_type.get_information(parser)
        return result

    def get_min_length_rule(self)->Rule:
        causes = [Cause(name=f"pdf.{self.name}.type", sentence=self.type)]
        return Rule.create_min_length(self.min_length, causes)

    def get_max_length_rule(self)->Rule:
        causes = [Cause(name=f"pdf.{self.name}.type", sentence=self.type)]
        return Rule.create_max_length(self.max_length, causes)

    def get_max_val_rule(self)->Rule:
        causes = [Cause(name=f"pdf.{self.name}.type", sentence=self.type)]
        return Rule.create_maximum(self.max_val, causes)

    def get_min_val_rule(self)->Rule:
        causes = [Cause(name=f"pdf.{self.name}.type", sentence=self.type)]
        return Rule.create_minimum(self.min_val, causes)

    def get_card_rule(self)->Rule:
        causes = [Cause(name=f"pdf.{self.name}.type", sentence=self.type)]
        return Rule.create_type(self.type, causes)

    def get_min_size_rule(self)->Rule:
        causes = [Cause(name=f"pdf.{self.name}.card", sentence=self.card)]
        if self.max_size == "1":
            if self.min_size == "1":
                return Rule.create_required(causes)
        else:
            return Rule.create_min_items(int(self.min_size), causes)

    def get_max_size_rule(self)->Rule:
        causes = [Cause(name=f"pdf.{self.name}.card", sentence=self.card)]
        return Rule.create_max_items(int(self.max_size), causes)

    def get_rule_list(self):
        result = []
        if self.max_val:
            result.append(self.get_max_val_rule())
        if self.min_val:
            result.append(self.get_min_val_rule())
        if self.min_length:
            result.append(self.get_min_length_rule())
        if self.max_length:
            result.append(self.get_max_length_rule())
        min_size_rule = self.get_min_size_rule()
        if min_size_rule:
            result.append(min_size_rule)
        if self.max_size != "*" and self.max_size != "1":
            result.append(self.get_max_size_rule())
        return result

    def get_min_length(self):
        match = re.search(r'\[(\d+)\.\.(\d+)\]', self.type)
        if match:
            return int(match.group(1))
        return None

    def get_max_length(self):
        match = re.search(r'\[(\d+)\.\.(\d+)\]', self.type)
        if match:
            return int(match.group(2))
        return None

    def get_min_val(self):
        # e.g., "0 <= val" or "0 <= val <="
        match = re.search(r'(\d+)\s*<=\s*val', self.type)
        if match:
            return int(match.group(1))
        return None

    def get_max_val(self):
        # e.g., "val <= 100"
        match = re.search(r'val\s*<=\s*(\d+)', self.type)
        if match:
            return int(match.group(1))
        return None