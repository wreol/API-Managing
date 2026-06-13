import os

from cryptography.hazmat.primitives.ciphers.aead import AESGCM


class EncryptionService:
    def __init__(self, key_bytes: bytes):
        if len(key_bytes) != 32:
            raise ValueError("Encryption key must be 32 bytes for AES-256-GCM")
        self._key = key_bytes

    def encrypt(self, plaintext: str) -> str:
        nonce = os.urandom(12)
        aesgcm = AESGCM(self._key)
        ciphertext = aesgcm.encrypt(nonce, plaintext.encode("utf-8"), None)
        combined = nonce + ciphertext
        return combined.hex()

    def decrypt(self, encrypted_hex: str) -> str:
        try:
            combined = bytes.fromhex(encrypted_hex)
            nonce = combined[:12]
            ciphertext = combined[12:]
            aesgcm = AESGCM(self._key)
            plaintext = aesgcm.decrypt(nonce, ciphertext, None)
            return plaintext.decode("utf-8")
        except Exception as exc:
            raise ValueError("Decryption failed: data may be tampered or corrupted") from exc

    @staticmethod
    def extract_prefix(key_value: str) -> str:
        parts = key_value.split("-")
        if len(parts) >= 2:
            return parts[0] + "-"
        return key_value[:3]

    @staticmethod
    def extract_last_4(key_value: str) -> str:
        return key_value[-4:]

    @staticmethod
    def mask_key(prefix: str, last_4: str) -> str:
        return f"{prefix}...****{last_4}"
