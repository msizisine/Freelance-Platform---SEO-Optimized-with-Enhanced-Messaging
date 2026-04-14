#!/usr/bin/env python3
"""
HTTPS Development Server for PWA Testing
Run this script to start the Django server with HTTPS support
"""

import os
import sys
import subprocess
import ssl
from http.server import HTTPServer, SimpleHTTPRequestHandler
from django.core.management import execute_from_command_line

def generate_self_signed_cert():
    """Generate self-signed certificate for HTTPS"""
    cert_path = 'cert.pem'
    key_path = 'key.pem'
    
    if os.path.exists(cert_path) and os.path.exists(key_path):
        print("Certificate already exists")
        return cert_path, key_path
    
    print("Generating self-signed certificate...")
    try:
        # Try to generate certificate using OpenSSL
        result = subprocess.run([
            'openssl', 'req', '-x509', '-newkey', 'rsa:2048',
            '-keyout', key_path, '-out', cert_path, '-days', '365',
            '-nodes', '-subj', '/CN=localhost'
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("Certificate generated successfully")
            return cert_path, key_path
        else:
            print("OpenSSL not available, creating simple certificate...")
            return create_simple_cert()
            
    except FileNotFoundError:
        print("OpenSSL not found, creating simple certificate...")
        return create_simple_cert()

def create_simple_cert():
    """Create a simple self-signed certificate using Python's ssl module"""
    from cryptography import x509
    from cryptography.x509.oid import NameOID
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import rsa
    import datetime
    
    # Generate private key
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )
    
    # Create certificate
    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.COUNTRY_NAME, "US"),
        x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "CA"),
        x509.NameAttribute(NameOID.LOCALITY_NAME, "San Francisco"),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, "pro4me"),
        x509.NameAttribute(NameOID.COMMON_NAME, "localhost"),
    ])
    
    cert = x509.CertificateBuilder().subject_name(
        subject
    ).issuer_name(
        issuer
    ).public_key(
        private_key.public_key()
    ).serial_number(
        x509.random_serial_number()
    ).not_valid_before(
        datetime.datetime.utcnow()
    ).not_valid_after(
        datetime.datetime.utcnow() + datetime.timedelta(days=365)
    ).add_extension(
        x509.SubjectAlternativeName([
            x509.DNSName("localhost"),
            x509.DNSName("127.0.0.1"),
        ]),
        critical=False,
    ).sign(private_key, hashes.SHA256())
    
    # Write certificate and key to files
    with open("cert.pem", "wb") as f:
        f.write(cert.public_bytes(serialization.Encoding.PEM))
    
    with open("key.pem", "wb") as f:
        f.write(private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        ))
    
    print("Simple certificate created")
    return "cert.pem", "key.pem"

def run_https_server():
    """Run Django server with HTTPS"""
    cert_path, key_path = generate_self_signed_cert()
    
    # Install django-extensions if not available
    try:
        import django_extensions
    except ImportError:
        print("Installing django-extensions...")
        subprocess.run([sys.executable, "-m", "pip", "install", "django-extensions"])
    
    # Add django-extensions to INSTALLED_APPS if not already there
    settings_file = 'freelance_platform/settings.py'
    with open(settings_file, 'r') as f:
        settings_content = f.read()
    
    if 'django_extensions' not in settings_content:
        with open(settings_file, 'w') as f:
            f.write(settings_content.replace(
                "INSTALLED_APPS = [",
                "INSTALLED_APPS = [\n    'django_extensions',"
            ))
    
    print(f"\n{'='*60}")
    print("PWA HTTPS Development Server")
    print("="*60)
    print(f"Certificate: {cert_path}")
    print(f"Private Key: {key_path}")
    print(f"Server will run at: https://127.0.0.1:8000")
    print(f"PWA Install URL: https://127.0.0.1:8000")
    print("\nNote: Browser will show security warning - this is normal for self-signed certs")
    print("Click 'Advanced' -> 'Proceed to 127.0.0.1 (unsafe)' to continue")
    print("="*60)
    
    # Run Django with HTTPS using runserver_plus
    try:
        execute_from_command_line(['manage.py', 'runserver_plus', '--cert', cert_path, '--key', key_path, '127.0.0.1:8000'])
    except SystemExit:
        print("\nIf runserver_plus fails, try:")
        print("pip install django-extensions Werkzeug")
        print("Then run this script again")

if __name__ == "__main__":
    run_https_server()
