from enum import Enum, auto

class ControllerStatus(Enum):
    WAIT_FOR_CSMS = auto()
    RUNNING = auto()