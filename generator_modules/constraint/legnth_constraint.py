


class LengthConstraint:
    def __init__(self, length:int, force:bool):
        self.length:int = length
        self.force:bool = force

    def set(self, length:int, force:bool):
        if self.force == True:
            return
        self.length: int = length
        self.force: bool = force

class MaxLengthConstraint(LengthConstraint):
    def __init__(self, length:int, force:bool):
        super().__init__(length,force)

    def set(self, length: int, force: bool):
        if self.force == True:
            return
        if force == True:
            self.length: int = length
            self.force: bool = force
        elif length < self.length:
            self.length: int = length
            self.force: bool = force

    @staticmethod
    def update(constraint, length: int, force: bool):
        if constraint is None:
            return MaxLengthConstraint(length=length, force=force)
        constraint.set(length, force)
        return constraint

class MinLengthConstraint(LengthConstraint):
    def __init__(self, length:int, force:bool):
        super().__init__(length,force)

    def set(self, length: int, force: bool):
        if self.force == True:
            return
        if force == True:
            self.length: int = length
            self.force: bool = force
        elif length > self.length:
            self.length: int = length
            self.force: bool = force

    @staticmethod
    def update(constraint, length: int, force: bool):
        if constraint is None:
            return MinLengthConstraint(length=length, force=force)
        constraint.set(length, force)
        return constraint