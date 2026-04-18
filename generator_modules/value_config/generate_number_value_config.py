import random
class GenerateNumberValueConfig:
    def __init__(self):
        self.max_decimal_places: int = 10
        self.required: bool = False
        self.is_determine_property = False

    def is_random_empty_value_status(self):
        return self.required == False and bool(random.getrandbits(1)) == False and self.is_determine_property == False