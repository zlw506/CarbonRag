import base64
import hashlib

from cryptography.fernet import Fernet, InvalidToken

from app.core.config import get_settings


def _build_fernet(secret: str | None = None) -> Fernet:
    material = (secret or get_settings().settings_encryption_key).encode("utf-8")
    derived_key = base64.urlsafe_b64encode(hashlib.sha256(material).digest())
    return Fernet(derived_key)


def encrypt_secret(value: str | None) -> str | None:
    if not value:
        return None
    return _build_fernet().encrypt(value.encode("utf-8")).decode("utf-8")


def decrypt_secret(value: str | None) -> str | None:
    if not value:
        return None
    try:
        return _build_fernet().decrypt(value.encode("utf-8")).decode("utf-8")
    except InvalidToken as exc:
        raise ValueError("Stored provider credential could not be decrypted.") from exc
