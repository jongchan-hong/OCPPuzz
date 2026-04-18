import random
class MAC:
    @staticmethod
    def generate_random_value() -> str:
        mac = [random.randint(0x00, 0xFF) for _ in range(6)]

        mac[0] = mac[0] & 0b11111110
        mac[0] = mac[0] | 0b00000010

        return ':'.join(f'{b:02x}' for b in mac)