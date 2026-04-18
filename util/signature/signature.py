import random
import base64
from cryptography.hazmat.primitives.asymmetric import rsa, padding, ec, ed25519, ed448
from cryptography.hazmat.primitives import hashes, serialization, hmac
import os
CITRINE_ENCODING_METHOD = [
        "SHA-1",
        "SHA-256",
        "SHA-384",
        "SHA-512"
    ]
CITRINE_SIGNED_METHOD = [
    'RSASSA-PKCS1-v1_5',
    'RSA-PSS',
    'ECDSA',
]
import os
import base64
from cryptography.hazmat.primitives.asymmetric import rsa, padding, ec
from cryptography.hazmat.primitives import hashes, serialization
class Signature:
    def __init__(self, signing_method, encoding_method, content: bytes = None, key_path: str = "signature/private_key.pem", password: bytes = None):
        self.content = content if content else os.urandom(32)
        self.signing_method = signing_method
        self.encoding_method = encoding_method
        self.key_path = key_path
        self.password = password

        self._prepare_private_key()
        self.signature = self._sign()

    def _prepare_private_key(self):
        if os.path.exists(self.key_path):
            self.private_key = self.load_private_key_from_pem(self.key_path, self.password)
        else:
            self._generate_keys()
            self.save_private_key_to_pem(self.key_path, self.password)

    def _generate_keys(self):
        if self.signing_method in ['RSASSA-PKCS1-v1_5', 'RSA-PSS']:
            self.private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        elif self.signing_method == 'ECDSA':
            self.private_key = ec.generate_private_key(ec.SECP256R1())
        else:
            raise ValueError(f"Unsupported signing method: {self.signing_method}")

    def _sign(self):
        match self.signing_method:
            case 'RSASSA-PKCS1-v1_5':
                return self.private_key.sign(
                    self.content,
                    padding.PKCS1v15(),
                    self._get_hash()
                )
            case 'RSA-PSS':
                return self.private_key.sign(
                    self.content,
                    padding.PSS(
                        mgf=padding.MGF1(self._get_hash()),
                        salt_length=padding.PSS.MAX_LENGTH,
                    ),
                    self._get_hash()
                )
            case 'ECDSA':
                return self.private_key.sign(
                    self.content,
                    ec.ECDSA(self._get_hash())
                )
            case _:
                raise ValueError(f"Unsupported signing method: {self.signing_method}")

    def _get_hash(self):
        return {
            "SHA-1": hashes.SHA1(),
            "SHA-256": hashes.SHA256(),
            "SHA-384": hashes.SHA384(),
            "SHA-512": hashes.SHA512(),
        }[self.encoding_method]

    def save_private_key_to_pem(self, path: str, password: bytes = None):
        print("do not SAVE@@@")
        exit()

        pem = self.private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.BestAvailableEncryption(password) if password else serialization.NoEncryption()
        )
        with open(path, "wb") as f:
            f.write(pem)
        self.export_public_key_pem("signature/public_key.pem")
        print(f"✅ Private key saved to {path}")

    @staticmethod
    def load_private_key_from_pem(path: str, password: bytes = None):
        with open(path, "rb") as f:
            pem_data = f.read()
        return serialization.load_pem_private_key(pem_data, password=password)

    def export_public_key_pem(self, public_key_path: str):
        public_pem = self.private_key.public_key().public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        with open(public_key_path, "wb") as f:
            f.write(public_pem)
        print(f"📤 Public key exported to {public_key_path}")

    def get_signature_base64(self):
        return base64.b64encode(self.signature).decode()

    def get_public_key_base64(self):
        der = self.private_key.public_key().public_bytes(
            encoding=serialization.Encoding.DER,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        return base64.b64encode(der).decode()

    def get_signed_meter_data(self):
        return base64.b64encode(self.signature).decode()

    def get_public_key(self, public_key_path: str = "signature/public_key.pem", base64_encode:bool = True):
        with open(public_key_path, "rb") as f:
            pem_data = f.read()

        public_key = serialization.load_pem_public_key(pem_data)
        der = public_key.public_bytes(
            encoding=serialization.Encoding.DER,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        if base64_encode:
            return base64.b64encode(der).decode()
        return der
