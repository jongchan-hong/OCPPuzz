class StandardizedComponent:
    def __init__(self, name, description):
        self.name = name.replace("\n", "")
        self.description = description.replace("\n", " ")