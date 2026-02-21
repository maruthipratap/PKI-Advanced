import datetime
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.x509 import ReasonFlags
from app.ca.intermediate_ca import load_intermediate_ca
from app.models.certificate_db import RevokedCertificate
from config import Config
import os


# Map reason string → cryptography ReasonFlags
REASON_MAP = {
    "Key Compromise":          ReasonFlags.key_compromise,
    "CA Compromise":           ReasonFlags.ca_compromise,
    "Affiliation Changed":     ReasonFlags.affiliation_changed,
    "Superseded":              ReasonFlags.superseded,
    "Cessation of Operation":  ReasonFlags.cessation_of_operation,
    "Privilege Withdrawn":     ReasonFlags.privilege_withdrawn,
    "No reason provided":      ReasonFlags.unspecified,
}


def generate_crl():
    """
    Build a proper signed CRL from all revoked certs in the database.
    Saves to storage/intermediate_ca/crl.pem and returns PEM string.
    """
    int_private_key, int_cert = load_intermediate_ca()

    now      = datetime.datetime.utcnow()
    next_update = now + datetime.timedelta(days=7)  # CRL valid for 7 days

    builder = (
        x509.CertificateRevocationListBuilder()
        .issuer_name(int_cert.subject)
        .last_update(now)
        .next_update(next_update)
    )

    # Pull all revoked certs from DB and add to CRL
    revoked_records = RevokedCertificate.query.all()

    for record in revoked_records:
        reason_flag = REASON_MAP.get(record.reason, ReasonFlags.unspecified)

        revoked_cert = (
            x509.RevokedCertificateBuilder()
            .serial_number(int(record.serial_number))
            .revocation_date(record.revoked_at)
            .add_extension(
                x509.CRLReason(reason_flag),
                critical=False
            )
            .build()
        )
        builder = builder.add_revoked_certificate(revoked_cert)

    # Sign CRL with Intermediate CA private key
    crl = builder.sign(int_private_key, hashes.SHA256())

    # Save as PEM file
    crl_path = os.path.join(Config.INTERMEDIATE_DIR, "crl.pem")
    crl_pem  = crl.public_bytes(serialization.Encoding.PEM)

    with open(crl_path, 'wb') as f:
        f.write(crl_pem)

    print(f"  [CRL] Generated with {len(revoked_records)} revoked certificate(s)")
    return crl_pem.decode('utf-8')


def get_crl_info():
    """Return CRL details as a dict for display."""
    crl_path = os.path.join(Config.INTERMEDIATE_DIR, "crl.pem")

    if not os.path.exists(crl_path):
        return None

    with open(crl_path, 'rb') as f:
        crl = x509.load_pem_x509_crl(f.read())

    return {
        "issuer":       crl.issuer.rfc4514_string(),
        "last_update":  crl.last_update_utc.strftime("%Y-%m-%d %H:%M UTC"),
        "next_update":  crl.next_update_utc.strftime("%Y-%m-%d %H:%M UTC"),
        "revoked_count": len(list(crl)),
        "pem_path":     crl_path,
    }