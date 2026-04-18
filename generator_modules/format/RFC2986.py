from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
import random
import string
from enum import Enum

class RFC2986:

    class Mode(Enum):
        Normal = 1
        BIG = 2

    @staticmethod
    def generate_random_value(target_length: int) -> str:
        def random_string(length):
            return ''.join(random.choices(string.ascii_letters, k=length))

        mode = RFC2986.Mode.Normal
        if target_length > 5500:
            mode = RFC2986.Mode.BIG

        key_size = 2048 if mode == RFC2986.Mode.Normal else 8192
        max_attempts = 30
        extra_unit = 20

        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=key_size
        )

        subject_base = [
            x509.NameAttribute(NameOID.COUNTRY_NAME, "US"),
            x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME,
                               random_string(8 if mode == RFC2986.Mode.Normal else 1000)),
            x509.NameAttribute(NameOID.LOCALITY_NAME,
                               random_string(6 if mode == RFC2986.Mode.Normal else 1000)),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME,
                               random_string(12 if mode == RFC2986.Mode.Normal else 1000)),
            x509.NameAttribute(NameOID.COMMON_NAME,
                               random_string(6 if mode == RFC2986.Mode.Normal else 50) + ".example.com"),
        ]

        final_csr = ""
        extra_len = 0

        for _ in range(max_attempts):
            filler = random_string(extra_len)
            subject = x509.Name(subject_base + [
                x509.NameAttribute(NameOID.ORGANIZATIONAL_UNIT_NAME, filler)
            ])

            csr = x509.CertificateSigningRequestBuilder().subject_name(
                subject
            ).sign(private_key, hashes.SHA256())

            csr_pem = csr.public_bytes(serialization.Encoding.PEM).decode()

            if len(csr_pem) >= target_length:
                return csr_pem[:target_length] if len(csr_pem) > target_length else csr_pem

            final_csr = csr_pem
            extra_len += extra_unit

        return final_csr