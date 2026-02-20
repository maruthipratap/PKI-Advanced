import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.crypto.key_manager import generate_and_save_keypair, load_private_key, load_public_key
from app.crypto.signer import sign_data, verify_signature
from config import Config

def test_key_generation():
    print("\n--- Testing Key Generation ---")
    priv, pub = generate_and_save_keypair(
        name="test_key",
        directory="storage/test",
        password=Config.CA_KEY_PASSWORD
    )
    print("  [OK] Keys generated")

    # Reload from file and verify they work
    loaded_priv = load_private_key("storage/test/test_key.key", Config.CA_KEY_PASSWORD)
    loaded_pub  = load_public_key("storage/test/test_key.pub")
    print("  [OK] Keys loaded from file")

    # Sign and verify
    message = b"PKI-Advanced test message"
    sig = sign_data(message, loaded_priv)
    result = verify_signature(message, sig, loaded_pub)

    assert result == True
    print("  [OK] Sign and verify works")

    # Tampered data should fail
    tampered = verify_signature(b"tampered data", sig, loaded_pub)
    assert tampered == False
    print("  [OK] Tampered data correctly rejected")

    print("\n ALL CRYPTO TESTS PASSED!")

if __name__ == '__main__':
    test_key_generation()