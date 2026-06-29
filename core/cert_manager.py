import datetime
import platform
import subprocess
from pathlib import Path

from cryptography import x509
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID

CERT_DIR = Path(__file__).parent.parent / 'certs'

# mitmproxy looks for these exact filenames in confdir
_CA_COMBINED = CERT_DIR / 'mitmproxy-ca.pem'       # key + cert (for mitmproxy)
CA_CERT_PATH  = CERT_DIR / 'mitmproxy-ca-cert.pem'  # cert only (for installation)


def generate_ca():
    CERT_DIR.mkdir(exist_ok=True)

    key = rsa.generate_private_key(
        public_exponent=65537, key_size=2048, backend=default_backend()
    )

    name = x509.Name([
        x509.NameAttribute(NameOID.COMMON_NAME,        'NetSentry Local CA'),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME,  'NetSentry'),
    ])

    cert = (
        x509.CertificateBuilder()
        .subject_name(name)
        .issuer_name(name)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.datetime.utcnow())
        .not_valid_after(datetime.datetime.utcnow() + datetime.timedelta(days=3650))
        .add_extension(x509.BasicConstraints(ca=True, path_length=None), critical=True)
        .sign(key, hashes.SHA256(), default_backend())
    )

    key_pem  = key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.TraditionalOpenSSL,
        serialization.NoEncryption()
    )
    cert_pem = cert.public_bytes(serialization.Encoding.PEM)

    _CA_COMBINED.write_bytes(key_pem + cert_pem)
    CA_CERT_PATH.write_bytes(cert_pem)


def install_ca_windows():
    if platform.system() != 'Windows':
        return
    subprocess.run(
        ['certutil', '-addstore', '-f', 'ROOT', str(CA_CERT_PATH)],
        check=True
    )


def uninstall_ca_windows():
    if platform.system() != 'Windows':
        return
    subprocess.run(
        ['certutil', '-delstore', 'ROOT', 'NetSentry Local CA'],
        check=True
    )


def ca_exists() -> bool:
    return _CA_COMBINED.exists() and CA_CERT_PATH.exists()
