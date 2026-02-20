import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # ─── Flask ───────────────────────────────────────────
    SECRET_KEY = os.environ.get('SECRET_KEY', 'pki-advanced-secret-2025')
    DEBUG = True

    # ─── MySQL ───────────────────────────────────────────
    MYSQL_USER     = os.environ.get('MYSQL_USER', 'root')
    MYSQL_PASSWORD = os.environ.get('MYSQL_PASSWORD', 'yourpassword')
    MYSQL_HOST     = os.environ.get('MYSQL_HOST', 'localhost')
    MYSQL_DB       = os.environ.get('MYSQL_DB', 'pki_advanced')

    SQLALCHEMY_DATABASE_URI = (
        f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}"
        f"@{MYSQL_HOST}/{MYSQL_DB}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # ─── Storage Paths ───────────────────────────────────
    BASE_DIR          = os.path.dirname(os.path.abspath(__file__))
    STORAGE_DIR       = os.path.join(BASE_DIR, 'storage')
    ROOT_CA_DIR       = os.path.join(STORAGE_DIR, 'root_ca')
    INTERMEDIATE_DIR  = os.path.join(STORAGE_DIR, 'intermediate_ca')
    ISSUED_DIR        = os.path.join(STORAGE_DIR, 'issued')

    # ─── CA Settings ─────────────────────────────────────
    CA_KEY_PASSWORD   = os.environ.get('CA_KEY_PASSWORD', 'ca-secret-pass').encode()
    CA_COUNTRY        = "IN"
    CA_STATE          = "Telangana"
    CA_CITY           = "Hyderabad"
    CA_ORG            = "PKI-Advanced"
    CA_UNIT           = "Security Lab"
    ROOT_CA_CN        = "PKI-Advanced Root CA"
    INTERMEDIATE_CN   = "PKI-Advanced Intermediate CA"

    # ─── Certificate Settings ─────────────────────────────
    CERT_VALIDITY_DAYS         = 365
    ROOT_CA_VALIDITY_DAYS      = 3650   # 10 years
    INTERMEDIATE_VALIDITY_DAYS = 1825   # 5 years