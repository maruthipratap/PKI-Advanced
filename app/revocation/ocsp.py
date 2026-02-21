from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.x509 import ocsp
from cryptography.x509.ocsp import OCSPCertStatus
from app.ca.intermediate_ca import load_intermediate_ca
from app.ca.root_ca import load_root_ca
from app.models.certificate_db import Certificate, RevokedCertificate
import datetime


def check_status_by_serial(serial_number: str):
    """
    Given a serial number string, return its OCSP-style status dict.
    This is the core logic used by the /ocsp route.
    """
    cert = Certificate.query.filter_by(serial_number=serial_number).first()

    if not cert:
        return {"status": "UNKNOWN", "serial": serial_number}

    if cert.status == "REVOKED":
        revoked = RevokedCertificate.query.filter_by(
            serial_number=serial_number
        ).first()
        return {
            "status":      "REVOKED",
            "serial":      serial_number,
            "owner":       cert.owner_name,
            "revoked_at":  revoked.revoked_at.strftime("%Y-%m-%d %H:%M UTC") if revoked else "unknown",
            "reason":      revoked.reason if revoked else "unspecified",
        }

    if cert.is_expired():
        return {
            "status":  "EXPIRED",
            "serial":  serial_number,
            "owner":   cert.owner_name,
            "expired": cert.valid_to.strftime("%Y-%m-%d %H:%M UTC"),
        }

    return {
        "status":   "GOOD",
        "serial":   serial_number,
        "owner":    cert.owner_name,
        "valid_to": cert.valid_to.strftime("%Y-%m-%d %H:%M UTC"),
    }


def build_ocsp_response(serial_number: str) -> dict:
    """
    Full OCSP-style response with CA info attached.
    Returns a structured dict ready for JSON response.
    """
    _, int_cert  = load_intermediate_ca()
    _, root_cert = load_root_ca()

    status = check_status_by_serial(serial_number)

    return {
        "ocsp_response": {
            "version":        "1.0",
            "responder":      int_cert.subject.rfc4514_string(),
            "produced_at":    datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
            "cert_status":    status,
            "this_update":    datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
            "next_update":    (datetime.datetime.utcnow() + datetime.timedelta(hours=1))
                              .strftime("%Y-%m-%d %H:%M:%S UTC"),
            "signature_alg":  "SHA256withRSA",
            "issuer_chain": {
                "intermediate": int_cert.subject.rfc4514_string(),
                "root":         root_cert.subject.rfc4514_string(),
            }
        }
    }