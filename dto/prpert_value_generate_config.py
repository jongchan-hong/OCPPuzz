
class PropertyValueGenerateConfig(object):
    def __init__(self, property_value, parent_key = None, parent_value = None, property_key= None, result= None, used_property_key_set= None, force_measurand = None, force_not_in_measurand_set = None):
        self.parent_key = parent_key
        self.parent_value = parent_value
        self.property_key = property_key
        self.property_value = property_value
        self.result = result
        self.used_property_key_set = used_property_key_set
        self.force_measurand = force_measurand
        self.force_not_in_measurand_set = force_not_in_measurand_set