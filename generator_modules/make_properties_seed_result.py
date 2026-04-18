from typing import List


class MakePropertiesSeedResult:
    def __init__(self, result:dict, wait_for_another_property_used_key_list=None, used_property_key_set=None
    ):
        if wait_for_another_property_used_key_list is None:
            wait_for_another_property_used_key_list = []
        if used_property_key_set is None:
            used_property_key_set = set()
        self.result = result
        self.wait_for_another_property_used_key_list = wait_for_another_property_used_key_list
        self.used_property_key_set = used_property_key_set