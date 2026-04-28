"""Windows DPAPI encryption for sensitive data."""

import json
from typing import Any, Optional

try:
    import win32crypt
except ImportError:
    win32crypt = None


def encrypt_data(data: str) -> bytes:
    """
    Encrypt data using Windows DPAPI.
    Falls back to plaintext if not on Windows or if win32crypt is unavailable.
    """
    if win32crypt is None:
        return data.encode("utf-8")

    try:
        return win32crypt.CryptEncryptData(
            data.encode("utf-8"), None, win32crypt.CRYPTPROTECT_UI_FORBIDDEN
        )
    except AttributeError:
        # Fallback if CryptEncryptData is not available (PyInstaller bundling issue)
        return data.encode("utf-8")


def decrypt_data(encrypted_data: bytes) -> Optional[str]:
    """
    Decrypt data using Windows DPAPI.
    Returns None if decryption fails.
    """
    if win32crypt is None:
        return encrypted_data.decode("utf-8")

    try:
        decrypted = win32crypt.CryptDecryptData(
            encrypted_data, None, win32crypt.CRYPTPROTECT_UI_FORBIDDEN
        )
        return decrypted.decode("utf-8")
    except (AttributeError, Exception):
        # Fallback if CryptDecryptData is not available or fails
        try:
            return encrypted_data.decode("utf-8")
        except Exception:
            return None


def encrypt_json(obj: Any) -> bytes:
    """Serialize and encrypt JSON object."""
    json_str = json.dumps(obj)
    return encrypt_data(json_str)


def decrypt_json(encrypted_data: bytes) -> Optional[Any]:
    """Decrypt and deserialize JSON object."""
    decrypted_str = decrypt_data(encrypted_data)
    if decrypted_str is None:
        return None

    try:
        return json.loads(decrypted_str)
    except json.JSONDecodeError:
        return None
