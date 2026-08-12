import base64
import hashlib
import os

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


def derive_key(password, salt):
    """Derive a secure encryption key from a password."""

    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=600000,
    )

    key = kdf.derive(password.encode())

    return base64.urlsafe_b64encode(key)


def encrypt_message(message, password):
    """Encrypt a message using a password."""

    salt = os.urandom(16)

    key = derive_key(password, salt)

    cipher = Fernet(key)

    encrypted_data = cipher.encrypt(
        message.encode()
    )

    message_hash = calculate_hash(
        message.encode()
    )

    return salt, encrypted_data, message_hash


def decrypt_message(
    encrypted_data,
    password,
    salt
):
    """Decrypt encrypted data."""

    key = derive_key(password, salt)

    cipher = Fernet(key)

    decrypted_data = cipher.decrypt(
        encrypted_data
    )

    return decrypted_data.decode()


def calculate_hash(data):
    """Generate SHA-256 hash."""

    return hashlib.sha256(data).hexdigest()


def verify_integrity(message, original_hash):
    """Verify message integrity."""

    current_hash = calculate_hash(
        message.encode()
    )

    return current_hash == original_hash