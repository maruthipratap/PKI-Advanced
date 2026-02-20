import os
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from config import Config


def generate_rsa_keypair():
    """Generate a 2048-bit RSA key pair."""
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )
    return private_key, private_key.public_key()


def save_private_key(private_key, filepath, password=None):
    """Save private key to file — encrypted if password given."""
    if password:
        encryption = serialization.BestAvailableEncryption(password)
    else:
        encryption = serialization.NoEncryption()

    pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=encryption
    )
    with open(filepath, 'wb') as f:
        f.write(pem)
    print(f"  [KEY] Private key saved: {filepath}")


def save_public_key(public_key, filepath):
    """Save public key to file."""
    pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
    with open(filepath, 'wb') as f:
        f.write(pem)
    print(f"  [KEY] Public key saved:  {filepath}")


def load_private_key(filepath, password=None):
    """Load private key from file."""
    with open(filepath, 'rb') as f:
        return serialization.load_pem_private_key(f.read(), password=password)


def load_public_key(filepath):
    """Load public key from file."""
    with open(filepath, 'rb') as f:
        return serialization.load_pem_public_key(f.read())


def generate_and_save_keypair(name, directory, password=None):
    """
    Full flow: generate + save both keys.
    Returns (private_key, public_key)
    """
    os.makedirs(directory, exist_ok=True)

    private_path = os.path.join(directory, f"{name}.key")
    public_path  = os.path.join(directory, f"{name}.pub")

    private_key, public_key = generate_rsa_keypair()

    save_private_key(private_key, private_path, password)
    save_public_key(public_key, public_path)

    return private_key, public_key