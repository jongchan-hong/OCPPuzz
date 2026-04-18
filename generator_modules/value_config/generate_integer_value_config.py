import random
import sys

from generator_modules.constraint.size_constraint import MinSizeConstraint, MaxSizeConstraint


class GenerateIntegerValueConfig:
    def __init__(self):
        self.max_decimal_places: int
        self.required: bool = False
        self.is_determine_property = False
        self.enum_integer_list = []
        self.except_integer_list = []
        self.min_size_constraint: MinSizeConstraint = MinSizeConstraint(-sys.maxsize - 1)
        self.max_size_constraint: MaxSizeConstraint = MaxSizeConstraint(sys.maxsize)
        self.start:int = None
        self.end:int = None
        self.stand_by_raise_exception = None

    def is_random_empty_value_status(self):
        return self.required == False and bool(random.getrandbits(1)) == False and self.is_determine_property == False