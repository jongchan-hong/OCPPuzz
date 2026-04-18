from enum import Enum
from typing import Optional
import random

class Charset(Enum):
    UTF8 = "utf-8"
    UTF16 = "utf-16"
    ASCII = "ascii"
    LATIN1 = "latin-1"
    EUC_KR = "euc-kr"
    CP949 = "cp949"
    SHIFT_JIS = "shift_jis"
    BIG5 = "big5"
    ISO8859_1 = "iso8859-1"

    @staticmethod
    def get_random_charset(except_charset: Optional["Charset"] = None):
        charset_list = list(Charset)

        if except_charset:
            charset_list = [c for c in charset_list if c != except_charset]

        if not charset_list:
            return None

        return random.choice(charset_list)