# PKI-Advanced 🔐

> **Enterprise-grade Public Key Infrastructure** built with Python, Flask, and MySQL.  
> Full X.509 certificate lifecycle management with role-based access control, audit logging, and real-time OCSP.

---

## 📌 Overview

PKI-Advanced is a fully functional Certificate Authority system that simulates real-world PKI infrastructure. It supports a complete certificate trust chain (Root CA → Intermediate CA → End-Entity), a request approval workflow, revocation services, and a multi-role web portal.

This project was built as an upgrade from a basic Java/Tomcat PKI system, rewritten in Python with a modern architecture and enterprise features.

> **Java version (basic):** [Public-Key-Infrastructure](https://github.com/maruthipratap/Public-Key-Infrasturcture)

---

## ✨ Features

### 🏛️ CA Hierarchy
- Self-signed **Root CA** (10-year validity)
- **Intermediate CA** signed by Root CA (5-year validity)
- End-entity certificates signed by Intermediate CA (1-year validity)
- Real **X.509 PEM format** — not Java serialization
- RSA 2048-bit keys, SHA256withRSA signatures
- Full X.509 extensions: BasicConstraints, KeyUsage, ExtendedKeyUsage, SAN, SubjectKeyIdentifier, AuthorityKeyIdentifier

### 👥 Role-Based Access Control (RBAC)
| Role | Permissions |
|------|-------------|
| **User** | Submit certificate requests, view own certs, download, renew |
| **Server Admin** | Server certificate management (portal) |
| **CA Admin** | Approve/reject requests, issue/revoke any cert, manage users, CRL, OCSP, audit logs |

### 📋 Certificate Request Workflow
```
User submits request → PENDING
        ↓
CA Admin reviews
        ↓
  APPROVED → Certificate auto-issued
  REJECTED → Reason shown to user
```

### 🚫 Revocation Services
- **CRL** (Certificate Revocation List) — signed PEM file, auto-regenerated on every revocation
- **OCSP** (Online Certificate Status Protocol) — real-time JSON endpoint at `/ocsp/<serial>`
- Reason codes: Key Compromise, CA Compromise, Superseded, Affiliation Changed, etc.

### 🔄 Certificate Renewal
- Renew any active or expired certificate in one click
- Old certificate automatically revoked as "Superseded"
- New serial number and 1-year validity issued immediately

### 🔍 Audit Logging
Every action is logged to MySQL with:
- Username, IP address, timestamp
- Action type (LOGIN, CERT_ISSUED, CERT_REVOKED, ROLE_CHANGED, etc.)
- Status (SUCCESS / FAILED)
- Certificate serial number (where applicable)

### 👤 Profile Management
- Update email address
- Change password (bcrypt hashed)
- View own certificate history

---

## 🛠️ Technology Stack

| Layer | Technology |
|-------|-----------|
| Language | Python 3.10+ |
| Web Framework | Flask |
| Cryptography | `cryptography` library (Bouncy Castle equivalent) |
| Database | MySQL + SQLAlchemy ORM |
| Auth | Flask-Login + Flask-Bcrypt |
| Certificate Format | PEM (X.509 standard) |
| Key Storage | Password-encrypted PEM files |
| Frontend | Jinja2 templates, custom dark UI |

---

## 📁 Project Structure

```
PKI-Advanced/
│
├── app/
│   ├── __init__.py              # Flask app factory, DB init, CA startup
│   ├── ca/
│   │   ├── root_ca.py           # Root CA generation (self-signed)
│   │   ├── intermediate_ca.py   # Intermediate CA (signed by Root)
│   │   └── certificate.py       # End-entity certificate issuance
│   ├── crypto/
│   │   ├── key_manager.py       # RSA key generation + encrypted storage
│   │   └── signer.py            # Sign and verify data/files
│   ├── revocation/
│   │   ├── crl_manager.py       # CRL generation (signed PEM)
│   │   └── ocsp.py              # OCSP responder logic
│   ├── auth/
│   │   ├── models.py            # User, Role models
│   │   ├── routes.py            # Login, logout, register, profile
│   │   └── decorators.py        # @login_required, @role_required
│   ├── audit/
│   │   ├── models.py            # AuditLog model
│   │   └── logger.py            # log_action() helper
│   ├── models/
│   │   └── certificate_db.py    # Certificate, RevokedCertificate models
│   ├── requests/
│   │   ├── models.py            # CertificateRequest model
│   │   └── routes.py            # Submit, approve, reject workflow
│   ├── routes/
│   │   ├── portal.py            # Landing page + 3 portals
│   │   ├── dashboard.py         # Certificate list + audit log
│   │   ├── issue.py             # Direct issue (CA admin)
│   │   ├── verify.py            # Certificate verification
│   │   ├── revoke.py            # Certificate revocation
│   │   ├── renew.py             # Certificate renewal
│   │   ├── admin.py             # User role management
│   │   └── crl_ocsp.py          # CRL download + OCSP endpoint
│   └── templates/               # Jinja2 HTML templates
│
├── storage/
│   ├── root_ca/                 # Root CA key + cert (auto-generated)
│   ├── intermediate_ca/         # Intermediate CA key + cert + CRL
│   └── issued/                  # End-entity private keys
│
├── config.py                    # App configuration + CA settings
├── run.py                       # Entry point
├── requirements.txt
└── .env                         # Environment variables (not committed)
```

---

## ⚙️ Setup & Installation

### Prerequisites
- Python 3.10+
- MySQL 8.0+
- Git

### 1. Clone the repository
```bash
git clone https://github.com/YOUR_USERNAME/PKI-Advanced.git
cd PKI-Advanced
```

### 2. Create virtual environment
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Mac/Linux
source venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Create MySQL database
```sql
CREATE DATABASE pki_advanced;
```

### 5. Create `.env` file
```env
SECRET_KEY=your-secret-key-here
MYSQL_USER=root
MYSQL_PASSWORD=your_mysql_password
MYSQL_HOST=localhost
MYSQL_DB=pki_advanced
CA_KEY_PASSWORD=your_ca_key_password
```

### 6. Run the application
```bash
python run.py
```

Visit: `http://localhost:5000`

---

## 🚀 First Run

On first startup, PKI-Advanced automatically:

1. Creates all MySQL tables
2. Seeds 3 roles: `user`, `server_admin`, `ca_admin`
3. Creates default CA admin account
4. Generates Root CA keypair + self-signed certificate
5. Generates Intermediate CA keypair + certificate signed by Root CA

**Default CA Admin credentials:**
```
Username: admin
Password: Admin@12345
```
> ⚠️ Change the password immediately after first login via Profile settings.

---

## 🖥️ Web Interface

| URL | Access | Description |
|-----|--------|-------------|
| `/` | All users | Landing page — 3 portal cards |
| `/portal/user` | All users | My requests, quick actions |
| `/portal/ca` | CA Admin | Stats, pending approvals, all certs |
| `/portal/server` | Server Admin | Server certificate management |
| `/request` | All users | Submit certificate request |
| `/requests/review` | CA Admin | Approve / reject pending requests |
| `/certificates` | All users | All certs with Active/Revoked/Expired filters |
| `/verify` | All users | Verify certificate by owner name |
| `/revoke` | CA Admin | Revoke any active certificate |
| `/renew/<id>` | Owner / CA Admin | Renew a certificate |
| `/crl` | All users | CRL viewer + download + OCSP form |
| `/ocsp/<serial>` | API | JSON OCSP response by serial number |
| `/admin/users` | CA Admin | Manage user roles and status |
| `/audit` | CA Admin | Full audit log with action filters |
| `/auth/profile` | All users | Update email, change password |

---

## 🔐 Certificate Chain

```
Root CA  (self-signed, 10 years)
    └── Intermediate CA  (signed by Root, 5 years)
            └── End-Entity Certificate  (signed by Intermediate, 1 year)
```

Each certificate includes:
- **BasicConstraints** — CA:TRUE for CAs, CA:FALSE for end-entity
- **KeyUsage** — digitalSignature, keyCertSign, crlSign (CA) / digitalSignature, keyEncipherment (user)
- **ExtendedKeyUsage** — clientAuth, emailProtection
- **SubjectAlternativeName** — DNS name + email
- **SubjectKeyIdentifier** + **AuthorityKeyIdentifier** — full chain tracing

---

## 📡 OCSP API

Query certificate status programmatically:

```bash
GET /ocsp/<serial_number>
```

**Example response:**
```json
{
  "ocsp_response": {
    "version": "1.0",
    "responder": "CN=PKI-Advanced Intermediate CA,...",
    "produced_at": "2026-02-21 10:30:00 UTC",
    "cert_status": {
      "status": "GOOD",
      "serial": "123456789",
      "owner": "John Doe",
      "valid_to": "2027-02-21 10:30:00 UTC"
    },
    "this_update": "2026-02-21 10:30:00 UTC",
    "next_update": "2026-02-21 11:30:00 UTC",
    "signature_alg": "SHA256withRSA"
  }
}
```

**Status values:** `GOOD` · `REVOKED` · `EXPIRED` · `UNKNOWN`

---

## 🔄 Certificate Workflow

```
1. User registers → assigned "user" role
2. User submits certificate request (owner name, email, org, purpose)
3. Request stored as PENDING in database
4. CA Admin logs in → reviews pending requests
5. CA Admin approves → X.509 certificate auto-generated and issued
   OR
   CA Admin rejects → rejection reason shown to user
6. User views certificate, downloads PEM
7. User or CA Admin can renew before/after expiry
8. CA Admin can revoke — certificate added to CRL, OCSP returns REVOKED
```

---

## 🗄️ Database Schema

```
users                  → id, username, email, password (bcrypt), role_id, is_active
roles                  → id, name (user / server_admin / ca_admin)
certificate_requests   → id, user_id, owner_name, email, org, purpose, status, reviewed_by
certificates           → id, serial_number, owner_name, email, org, issued_by, valid_from, valid_to, status, cert_pem
revoked_certificates   → id, serial_number, owner_name, revoked_at, reason
audit_logs             → id, user_id, username, action, detail, certificate_serial, ip_address, timestamp, status
```

---

## 📊 Comparison: Java Version vs Python Version

| Feature | Java Version | Python Version |
|---------|-------------|----------------|
| Certificate format | Java serialization | Real X.509 PEM |
| Key storage | Plaintext Base64 | Password-encrypted PEM |
| CA hierarchy | Single CA | Root → Intermediate → End-entity |
| User management | None | Registration, login, RBAC |
| Request workflow | Instant issue | Pending → Approved/Rejected |
| Expiry check | ❌ Missing | ✅ Full check |
| CRL format | Plain text file | Signed X.509 CRL PEM |
| OCSP | ❌ None | ✅ JSON API endpoint |
| Audit logging | ❌ None | ✅ Full audit trail in DB |
| Certificate renewal | ❌ None | ✅ One-click renewal |
| Database | File system | MySQL with ORM |
| Web framework | Tomcat servlets | Flask with blueprints |

---

## 🧪 Running Tests

```bash
python tests/test_crypto.py
```

Tests cover:
- RSA key pair generation
- Encrypted key save/load
- Sign and verify data
- Tampered data rejection

---

## 🔒 Security Notes

- Private keys are stored **password-encrypted** (never plaintext)
- Passwords hashed with **bcrypt**
- CA private keys are **never exposed** via web interface
- `.env` file is in `.gitignore` — credentials never committed
- `storage/*/` private keys are in `.gitignore`
- Session management via Flask-Login
- All critical actions logged to audit table with IP address

---

## 📅 Development Journey

| Phase | What Was Built |
|-------|---------------|
| Phase 1 | Flask app factory, MySQL connection, CA hierarchy auto-init |
| Phase 2 | RSA key manager (encrypted), digital signer |
| Phase 3 | Root CA + Intermediate CA with real X.509 extensions |
| Phase 4 | Certificate issuance, MySQL models, Flask routes |
| Phase 5 | Full dark-themed web UI (Jinja2 templates) |
| Phase 6 | CRL manager (signed PEM) + OCSP responder |
| Phase 7 | User auth (bcrypt), Flask-Login, role system |
| Phase 8 | RBAC decorators, 3-portal landing page |
| Phase 9 | Certificate request workflow (Pending→Approved/Rejected) |
| Phase 10 | Audit logging system |
| Phase 11 | Certificate renewal, filtered dashboard, user role management |
| Phase 12 | Bug fixes — rejection reasons, OCSP UI, server portal |

---

## 📄 License

This project is for educational purposes as part of a cybersecurity / PKI learning project.

---

## 👤 Author

**Maruthi Pratap**  
Python · Flask · Cryptography · PKI  
[GitHub](https://github.com/maruthipratap)