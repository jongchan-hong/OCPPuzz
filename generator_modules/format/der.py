import random
import string
from pyasn1.type.univ import Integer, OctetString, Sequence
from pyasn1.codec.der.encoder import encode
import random

class DER:
    @staticmethod
    def generate_fixed_length(length: int) -> bytes:
        class CustomSequence(Sequence):
            componentType = Sequence.componentType.clone()
            componentType[0] = Integer()
            componentType[1] = OctetString()

        for octet_len in range(1, length):
            for int_value in range(0, 9999999):
                obj = CustomSequence()
                obj.setComponentByPosition(0, int_value)
                obj.setComponentByPosition(1, OctetString(bytes([random.randint(0, 255) for _ in range(octet_len)])))

                encoded = encode(obj)

                if len(encoded) == length:
                    return encoded

        raise ValueError(f"Cannot generate DER of exact length {length}")