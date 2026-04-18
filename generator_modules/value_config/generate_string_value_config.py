from typing import Optional, List

from constants.charset import Charset
from constants.date_time_format import DateTimeFormat
from constants.format import Format
from generator_modules.constraint.format_constraint import FormatConstraint
from generator_modules.constraint.legnth_constraint import MinLengthConstraint, MaxLengthConstraint
import random

from generator_modules.constraint.population_constraint import PopulationConstraint


class GenerateStringValueConfig:
    DEFAULT_MIN_LENGTH = 0
    DEFAULT_MAX_LENGTH = 12000

    def __init__(self, printable):
        self.max_decimal_places: int
        self.active_enum = True
        self.required = False
        self.enum_list = []
        self.equal_value = None
        self.signature = None
        self.except_string_list = []
        self.is_determine_property = False
        self.charset: Charset = None
        self.not_allow_prefix_set = set()
        self.allow_prefix_set = set()
        self.population_constraint: PopulationConstraint = PopulationConstraint(printable)
        self.format_constraint: FormatConstraint = None
        self.format: Optional[Format] = None
        self.date_time_format: Optional[DateTimeFormat] = None
        self.allowed_characters: Optional[List[str]] = None
        self.not_allowed_characters = []
        self.min_length_constraint: MinLengthConstraint = None
        self.max_length_constraint: MaxLengthConstraint = None
        self.base64_encoding = False
        self.required_characters = []
        self.citrine_token_save = False
        self.citrine_token_delete = False
        self.empty_string = False
        self.remove = False
        self.byte_fix_excluded_lengths = None

    def set_format_constraint(self, format:Format, force:bool = False):
        if self.format_constraint is None:
            self.format_constraint = FormatConstraint(format, force)
        else:
            self.format_constraint.set(format, force)

    def is_random_empty_value_status(self):
        return self.required == False and bool(random.getrandbits(1)) == False and self.is_determine_property == False

    def is_enum_string(self):
        return self.enum_list and self.active_enum == True

    def get_equal_value(self):
        if self.active_enum == False:
            return None
        if not self.equal_value:
            return None
        if self.except_string_list and self.equal_value in self.except_string_list:
            return None
        if self.not_allowed_characters and any(char in self.equal_value for char in self.not_allowed_characters):
            return None
        return self.equal_value


    def get_random_enum_value(self):
        if self.except_string_list:
            if self.min_length_constraint and self.min_length_constraint.length:
                self.enum_list = [item for item in self.enum_list if item not in self.except_string_list and len(item) >= self.min_length_constraint.length]
            else:
                self.enum_list = [item for item in self.enum_list if item not in self.except_string_list]
        if self.not_allowed_characters:
            self.enum_list = [
                item for item in self.enum_list
                if not any(char in item for char in self.not_allowed_characters)
            ]
        if len(self.enum_list) > 0:
            return random.choice(self.enum_list)
        else:
            return "".join(random.choices(self.population_constraint.value, k=self.get_generate_value_random_length()))

    def get_generate_value_random_length(self):
        min_value = self.DEFAULT_MIN_LENGTH if self.min_length_constraint is None else self.min_length_constraint.length
        max_value = self.DEFAULT_MAX_LENGTH if self.max_length_constraint is None else self.max_length_constraint.length

        if max_value < min_value:
            max_value = min_value + 10
        length = random.randint(min_value, max_value)
        if self.base64_encoding == True:
            length = ((length * 3) // 4)
        return length
