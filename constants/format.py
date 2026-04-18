from enum import Enum, auto

class Format(Enum):
    URL = auto()
    PEM = auto()
    HEX = auto()
    HEX_NOT_ZERO_FILL = auto()
    NUMBER = auto()
    DATE_TIME = auto()
    RFC3339 = auto()
    UTF8 = auto()
    RFC5646 = auto()
    HTML = auto()
    RFC2986 = auto()
    MAC = auto()
    DER = auto()
    NOTHING = auto()