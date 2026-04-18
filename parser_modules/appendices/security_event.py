class SecurityEvent:
    def __init__(self, name, description, critical):
        self.name = name.replace("\n", "")
        self.description = description
        self.critical = critical