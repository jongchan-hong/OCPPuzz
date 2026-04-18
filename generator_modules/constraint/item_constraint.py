
class ItemConstraint:
    def __init__(self, size:int, force:bool):
        self.size:int = size
        self.force:bool = force

    def set(self, size:int, force:bool):
        if self.force == True:
            return
        self.size: int = size
        self.force: bool = force

class MaxItemConstraint(ItemConstraint):
    def __init__(self, size:int, force:bool):
        super().__init__(size,force)

    def set(self, size: int, force: bool):
        if self.force == True:
            return
        if force == True:
            self.size: int = size
            self.force: bool = force
        elif size < self.size:
            self.size: int = size
            self.force: bool = force

    @staticmethod
    def update(constraint, size: int, force: bool):
        if constraint is None or isinstance(constraint, MaxItemConstraint) == False:
            return MaxItemConstraint(size=size, force=force)
        constraint.set(size, force)
        return constraint

class MinItemConstraint(ItemConstraint):
    def __init__(self, size:int, force:bool):
        super().__init__(size,force)

    def set(self, size: int, force: bool):
        if self.force == True:
            return
        if force == True:
            self.size: int = size
            self.force: bool = force
        elif size > self.size:
            self.size: int = size
            self.force: bool = force

    @staticmethod
    def update(constraint, size: int, force: bool):
        if constraint is None or isinstance(constraint, MinItemConstraint) == False:
            return MinItemConstraint(size=size, force=force)
        constraint.set(size, force)
        return constraint