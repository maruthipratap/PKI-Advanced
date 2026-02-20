import os
import datetime
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes, serialization
from app.crypto.key_manager import generate_and_save_keypair, load_private_key
from app.ca.root_ca import load_root_ca
from config import Config


def generate_intermediate_ca():
    """
    Generate Intermediate CA keypair + certificate signed by Root CA.
    Only run ONCE — skips if already exists.
    """
    cert_path = os.path.join(Config.INTERMEDIATE_DIR, "intermediate.crt")
    key_path  = os.path.join(Config.INTERMEDIATE_DIR, "intermediate.key")

    if os.path.exists(cert_path) and os.path.exists(key_path):
        print("  [INTERMEDIATE CA] Already exists, skipping.")
        return load_intermediate_ca()

    print("  [INTERMEDIATE CA] Generating keypair...")
    private_key, public_key = generate_and_save_keypair(
        name="intermediate",
        directory=Config.INTERMEDIATE_DIR,
        password=Config.CA_KEY_PASSWORD
    )

    # Load Root CA to sign this certificate
    root_private_key, root_cert = load_root_ca()

    subject = x509.Name([
        x509.NameAttribute(NameOID.COUNTRY_NAME,             Config.CA_COUNTRY),
        x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME,   Config.CA_STATE),
        x509.NameAttribute(NameOID.LOCALITY_NAME,            Config.CA_CITY),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME,        Config.CA_ORG),
        x509.NameAttribute(NameOID.ORGANIZATIONAL_UNIT_NAME, Config.CA_UNIT),
        x509.NameAttribute(NameOID.COMMON_NAME,              Config.INTERMEDIATE_CN),
    ])

    now = datetime.datetime.utcnow()

    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(root_cert.subject)       # Issued BY Root CA
        .public_key(public_key)
        .serial_number(x509.random_serial_number())
        .not_valid_before(now)
        .not_valid_after(now + datetime.timedelta(days=Config.INTERMEDIATE_VALIDITY_DAYS))

        # This is also a CA but can only sign end-entity certs (path_length=0)
        .add_extension(
            x509.BasicConstraints(ca=True, path_length=0),
            critical=True
        )
        .add_extension(
            x509.KeyUsage(
                digital_signature=True,
                key_cert_sign=True,
                crl_sign=True,
                content_commitment=False,
                key_encipherment=False,
                data_encipherment=False,
                key_agreement=False,
                encipher_only=False,
                decipher_only=False
            ),
            critical=True
        )
        .add_extension(
            x509.SubjectKeyIdentifier.from_public_key(public_key),
            critical=False
        )
        .add_extension(
            x509.AuthorityKeyIdentifier.from_issuer_public_key(root_cert.public_key()),
            critical=False
        )
        # Signed by ROOT CA private key
        .sign(root_private_key, hashes.SHA256())
    )

    with open(cert_path, 'wb') as f:
        f.write(cert.public_bytes(serialization.Encoding.PEM))

    print(f"  [INTERMEDIATE CA] Certificate saved: {cert_path}")
    print(f"  [INTERMEDIATE CA] Signed by: {root_cert.subject.get_attributes_for_oid(NameOID.COMMON_NAME)[0].value}")

    return private_key, cert


def load_intermediate_ca():
    """Load existing Intermediate CA key and certificate."""
    key_path  = os.path.join(Config.INTERMEDIATE_DIR, "intermediate.key")
    cert_path = os.path.join(Config.INTERMEDIATE_DIR, "intermediate.crt")

    private_key = load_private_key(key_path, Config.CA_KEY_PASSWORD)

    with open(cert_path, 'rb') as f:
        cert = x509.load_pem_x509_certificate(f.read())

    return private_key, cert


def get_intermediate_ca_info():
    """Return Intermediate CA certificate details as a dict."""
    _, cert = load_intermediate_ca()
    return {
        "subject":    cert.subject.get_attributes_for_oid(NameOID.COMMON_NAME)[0].value,
        "issuer":     cert.issuer.get_attributes_for_oid(NameOID.COMMON_NAME)[0].value,
        "serial":     str(cert.serial_number),
        "valid_from": cert.not_valid_before_utc.strftime("%Y-%m-%d %H:%M:%S UTC"),
        "valid_to":   cert.not_valid_after_utc.strftime("%Y-%m-%d %H:%M:%S UTC"),
        "is_ca":      True
    }