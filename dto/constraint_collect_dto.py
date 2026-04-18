from typing import List, Optional, Any
from pydantic import BaseModel, ConfigDict, PrivateAttr

from copy import deepcopy

class Condition(BaseModel):
    attribute: str
    target: Optional[str] = None
    operator: str
    values: List[Any]
    def __eq__(self, other):
        if isinstance(other, Condition):
            return self.target == other.target and self.operator == other.operator and self.values == other.values and self.attribute == other.attribute
        return False

    def __hash__(self):
        return hash((self.target, self.operator, tuple(self.values), self.attribute))

    def get_target_name(self):
        return self.target.split(".")[-1]

class Constraint(BaseModel):
    attribute: str
    operator: str
    values: List[Any]

    def __eq__(self, other):
        if isinstance(other, Constraint):
            return self.attribute == other.attribute and self.operator == other.operator and set(self.values) == set(other.values)
        return False

    def __hash__(self):
        return hash((self.attribute, self.operator, tuple(sorted(self.values))))

class Cause(BaseModel):
    name: str
    sentence: str

    def __eq__(self, other):
        if isinstance(other, Cause):
            return self.name == other.name and self.sentence == other.sentence
        return False

    def __hash__(self):
        return hash((self.name, self.sentence))

class Rule(BaseModel):
    model_config = ConfigDict(ignored_types=(type(None),))
    causes: List[Cause]
    conditions: Optional[List[Condition]] = None
    constraint: Optional[Constraint]
    _generate_rule_entity = PrivateAttr(None)

    def clone(self):
        return Rule(
            causes=deepcopy(self.causes),
            conditions=deepcopy(self.conditions) if self.conditions is not None else None,
            constraint=deepcopy(self.constraint) if self.constraint is not None else None,
        )

    def get_id(self):
        return self._generate_rule_entity.id

    def __eq__(self, other):
        if isinstance(other, Rule):
            return self.conditions == other.conditions and self.constraint == other.constraint
        return False

    def __hash__(self):
        return hash((tuple(self.conditions or ()), self.constraint))

    @staticmethod
    def create_enum(enum: List[str], causes:List[Cause]):
        return Rule(
            causes=causes,
            constraint= Constraint(
                attribute="value",
                operator="in",
                values=enum
            )
        )

    @staticmethod
    def create_type(type: str, causes:List[Cause]):
        return Rule (
            causes=causes,
            constraint= Constraint(
                attribute="type",
                operator="equal",
                values=[type]
            )
        )

    @staticmethod
    def create_format(format: str, causes: List[Cause]):
        return Rule(
            causes=causes,
            constraint=Constraint(
                attribute="format",
                operator="equal",
                values=[format]
            )
        )

    @staticmethod
    def create_java_type(java_type: str, causes:List[Cause]):
        return Rule(
            causes=causes,
            constraint= Constraint(
                attribute="javaType",
                operator="equal",
                values=[java_type]
            )
        )

    @staticmethod
    def create_required(causes:List[Cause]):
        return Rule(
            causes=causes,
            constraint= Constraint(
                attribute="required",
                operator="equal",
                values=["true"]
            )
        )

    @staticmethod
    def create_max_length(length: int, causes:List[Cause]):
        return Rule(
            causes=causes,
            constraint= Constraint(
                attribute="maxLength",
                operator="equal",
                values=[length]
            )
        )

    @staticmethod
    def create_min_length(length: int, causes:List[Cause]):
        return Rule(
            causes=causes,
            constraint=Constraint(
                attribute="minLength",
                operator="equal",
                values=[length]
            )
        )

    @staticmethod
    def create_min_items(size: int, causes:List[Cause]):
        return Rule(
            causes=causes,
            constraint=Constraint(
                attribute="minItems",
                operator="equal",
                values=[size]
            )
        )

    @staticmethod
    def create_max_items(size: int, causes:List[Cause]):
        return Rule(
            causes=causes,
            constraint=Constraint(
                attribute="maxItems",
                operator="equal",
                values=[size]
            )
        )

    @staticmethod
    def create_minimum(size: int, causes:List[Cause]):
        return Rule(
            causes=causes,
            constraint=Constraint(
                attribute="minimum",
                operator="equal",
                values=[size]
            )
        )

    @staticmethod
    def create_maximum(size: int, causes: List[Cause]):
        return Rule(
            causes=causes,
            constraint=Constraint(
                attribute="maximum",
                operator="equal",
                values=[size]
            )
        )

class ConstraintCollectDTO(BaseModel):
    name: str
    rules: List[Rule]

class PageRange(BaseModel):
    start: int
    end: int

class AdditionalPageRequest(BaseModel):
    document: Optional[str] = "Specification"
    page_range: PageRange

class RuleExtractionResult(BaseModel):
    additional_page_request_list: Optional[List[AdditionalPageRequest]] = None
    rules: Optional[List[ConstraintCollectDTO]] = None