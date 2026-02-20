from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
import base64


def sign_data(data: bytes, private_key) -> str:
    """Sign data with private key. Returns base64 signature string."""
    signature = private_key.sign(
        data,
        padding.PKCS1v15(),
        hashes.SHA256()
    )
    return base64.b64encode(signature).decode('utf-8')


def verify_signature(data: bytes, signature_b64: str, public_key) -> bool:
    """Verify a base64 signature against data using public key."""
    try:
        signature = base64.b64decode(signature_b64)
        public_key.verify(
            signature,
            data,
            padding.PKCS1v15(),
            hashes.SHA256()
        )
        return True
    except Exception:
        return False


def sign_file(filepath: str, private_key) -> str:
    """Read a file and sign its contents."""
    with open(filepath, 'rb') as f:
        data = f.read()
    return sign_data(data, private_key)


def verify_file(filepath: str, signature_b64: str, public_key) -> bool:
    """Verify signature of a file."""
    with open(filepath, 'rb') as f:
        data = f.read()
    return verify_signature(data, signature_b64, public_key)