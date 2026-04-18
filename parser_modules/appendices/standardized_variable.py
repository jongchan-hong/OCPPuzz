class StandardizedVariable:
    def __init__(self, name, data_type, unit, description):
        self.name = name.replace("\n", "")
        self.data_type = data_type.replace("\n", "")
        self.unit = unit.replace("\n", "")
        self.description = description.replace("\n", " ")