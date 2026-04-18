class PopulationConstraint():
    def __init__(self, value, level = 1):
        self.value = value
        self.level = level

    def set(self, value, level):
        if self.level > level:
            return
        self.value = value
        self.level = level