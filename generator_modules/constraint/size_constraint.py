


class SizeConstraint:
    def __init__(self, size:int, force:bool = False):
        self.size:int = size
        self.force:bool = force

    def set(self, size:int, force:bool):
        if self.force == True:
            return
        self.size: int = size
        self.force: bool = force

class MaxSizeConstraint(SizeConstraint):
    def __init__(self, size:int, force:bool = False):
        super().__init__(size,force)

    def set(self, size: int, force: bool = False):
        if self.force == True:
            return
        if force == True:
            self.size: int = size
            self.force: bool = force
        elif size < self.size:
            self.size: int = size
            self.force: bool = force

class MinSizeConstraint(SizeConstraint):
    def __init__(self, size:int, force:bool = False):
        super().__init__(size,force)

    def set(self, size: int, force: bool = False):
        if self.force == True:
            return
        if force == True:
            self.size: int = size
            self.force: bool = force
        elif size > self.size:
            self.size: int = size
            self.force: bool = force