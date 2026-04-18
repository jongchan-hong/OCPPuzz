from constants.format import Format


class FormatConstraint():
    def __init__(self, value:Format, force:bool = False):
        self.value = value
        self.force = force

    def set(self, value: Format, force: bool = False):
        if self.force == True:
            return
        if not (self.value == Format.RFC2986 and value == Format.PEM):
            self.value: Format = value
            self.force: bool = force