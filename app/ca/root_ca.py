import os
import datetime
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes, serialization
from app.crypto.key_manager import generate_and_save_keypair, load_private_key
from config import Config


def generate_root_ca():
    """
    Generate Root CA keypair + self-signed certificate.
    Only run ONCE — skips if already exists.
    """
    cert_path = os.path.join(Config.ROOT_CA_DIR, "root_ca.crt")
    key_path  = os.path.join(Config.ROOT_CA_DIR, "root_ca.key")

    if os.path.exists(cert_path) and os.path.exists(key_path):
        print("  [ROOT CA] Already exists, skipping generation.")
        return load_root_ca()

    print("  [ROOT CA] Generating Root CA keypair...")
    private_key, public_key = generate_and_save_keypair(
        name="root_ca",
        directory=Config.ROOT_CA_DIR,
        password=Config.CA_KEY_PASSWORD
    )

    # Build certificate subject & issuer (same for self-signed)
    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.COUNTRY_NAME,             Config.CA_COUNTRY),
        x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME,   Config.CA_STATE),
        x509.NameAttribute(NameOID.LOCALITY_NAME,            Config.CA_CITY),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME,        Config.CA_ORG),
        x509.NameAttribute(NameOID.ORGANIZATIONAL_UNIT_NAME, Config.CA_UNIT),
        x509.NameAttribute(NameOID.COMMON_NAME,              Config.ROOT_CA_CN),
    ])

    now = datetime.datetime.utcnow()

    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(public_key)
        .serial_number(x509.random_serial_number())
        .not_valid_before(now)
        .not_valid_after(now + datetime.timedelta(days=Config.ROOT_CA_VALIDITY_DAYS))

        # Mark this as a CA certificate
        .add_extension(
            x509.BasicConstraints(ca=True, path_length=1),
            critical=True
        )
        # Key usage for a CA
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
        # Subject Key Identifier
        .add_extension(
            x509.SubjectKeyIdentifier.from_public_key(public_key),
            critical=False
        )
        # Self-signed: sign with its own private key
        .sign(private_key, hashes.SHA256())
    )

    # Save certificate as PEM
    with open(cert_path, 'wb') as f:
        f.write(cert.public_bytes(serialization.Encoding.PEM))

    print(f"  [ROOT CA] Certificate saved: {cert_path}")
    print(f"  [ROOT CA] Valid for 10 years until: {cert.not_valid_after_utc}")

    return private_key, cert


def load_root_ca():
    """Load existing Root CA key and certificate from disk."""
    key_path  = os.path.join(Config.ROOT_CA_DIR, "root_ca.key")
    cert_path = os.path.join(Config.ROOT_CA_DIR, "root_ca.crt")

    private_key = load_private_key(key_path, Config.CA_KEY_PASSWORD)

    with open(cert_path, 'rb') as f:
        cert = x509.load_pem_x509_certificate(f.read())

    return private_key, cert


def get_root_ca_info():
    """Return Root CA certificate details as a dict for display."""
    _, cert = load_root_ca()
    return {
        "subject":    cert.subject.get_attributes_for_oid(NameOID.COMMON_NAME)[0].value,
        "issuer":     cert.issuer.get_attributes_for_oid(NameOID.COMMON_NAME)[0].value,
        "serial":     str(cert.serial_number),
        "valid_from": cert.not_valid_before_utc.strftime("%Y-%m-%d %H:%M:%S UTC"),
        "valid_to":   cert.not_valid_after_utc.strftime("%Y-%m-%d %H:%M:%S UTC"),
        "is_ca":      True
    }