import os
import datetime
from cryptography import x509
from cryptography.x509.oid import NameOID, ExtendedKeyUsageOID
from cryptography.hazmat.primitives import hashes, serialization
from app.crypto.key_manager import generate_rsa_keypair, save_private_key
from app.ca.intermediate_ca import load_intermediate_ca
from config import Config


def issue_certificate(owner_name, email=None, organization=None):
    """
    Issue a signed end-entity certificate for a user.
    Signed by Intermediate CA.
    Returns (cert_pem_string, serial_number, valid_from, valid_to)
    """
    # Generate a fresh keypair for this user
    user_private_key, user_public_key = generate_rsa_keypair()

    # Save user private key to storage/issued/
    safe_name = owner_name.replace(" ", "_")
    user_key_path = os.path.join(Config.ISSUED_DIR, f"{safe_name}.key")
    save_private_key(user_private_key, user_key_path, Config.CA_KEY_PASSWORD)

    # Load Intermediate CA to sign this cert
    int_private_key, int_cert = load_intermediate_ca()

    # Build subject for end-entity
    name_attrs = [
        x509.NameAttribute(NameOID.COUNTRY_NAME,           Config.CA_COUNTRY),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME,      organization or Config.CA_ORG),
        x509.NameAttribute(NameOID.COMMON_NAME,            owner_name),
    ]
    if email:
        name_attrs.append(x509.NameAttribute(NameOID.EMAIL_ADDRESS, email))

    subject = x509.Name(name_attrs)

    now       = datetime.datetime.utcnow()
    valid_to  = now + datetime.timedelta(days=Config.CERT_VALIDITY_DAYS)

    # Build SAN (Subject Alternative Name)
    san_entries = [x509.DNSName(safe_name.lower())]
    if email:
        san_entries.append(x509.RFC822Name(email))

    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(int_cert.subject)          # Issued BY Intermediate CA
        .public_key(user_public_key)
        .serial_number(x509.random_serial_number())
        .not_valid_before(now)
        .not_valid_after(valid_to)

        # End-entity: NOT a CA
        .add_extension(
            x509.BasicConstraints(ca=False, path_length=None),
            critical=True
        )
        # Key usage for a regular user cert
        .add_extension(
            x509.KeyUsage(
                digital_signature=True,
                content_commitment=True,
                key_encipherment=True,
                data_encipherment=False,
                key_agreement=False,
                key_cert_sign=False,
                crl_sign=False,
                encipher_only=False,
                decipher_only=False
            ),
            critical=True
        )
        # Extended key usage
        .add_extension(
            x509.ExtendedKeyUsage([
                ExtendedKeyUsageOID.CLIENT_AUTH,
                ExtendedKeyUsageOID.EMAIL_PROTECTION,
            ]),
            critical=False
        )
        # Subject Alternative Names
        .add_extension(
            x509.SubjectAlternativeName(san_entries),
            critical=False
        )
        .add_extension(
            x509.SubjectKeyIdentifier.from_public_key(user_public_key),
            critical=False
        )
        .add_extension(
            x509.AuthorityKeyIdentifier.from_issuer_public_key(int_cert.public_key()),
            critical=False
        )
        # Signed by Intermediate CA
        .sign(int_private_key, hashes.SHA256())
    )

    cert_pem      = cert.public_bytes(serialization.Encoding.PEM).decode('utf-8')
    serial_number = str(cert.serial_number)

    print(f"  [CERT] Issued certificate for: {owner_name}")
    print(f"  [CERT] Serial: {serial_number[:20]}...")
    print(f"  [CERT] Valid until: {valid_to}")

    return cert_pem, serial_number, now, valid_to