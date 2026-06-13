import pytest

from app.services.encryption_service import EncryptionService


def test_encrypt_and_decrypt_roundtrip():
    svc = EncryptionService(key_bytes=b"test-key-12345678901234567890123")
    plaintext = "sk-proj-abc123xyz"

    encrypted = svc.encrypt(plaintext)
    assert encrypted != plaintext
    assert "sk-proj" not in encrypted

    decrypted = svc.decrypt(encrypted)
    assert decrypted == plaintext


def test_encrypt_different_each_time():
    svc = EncryptionService(key_bytes=b"test-key-12345678901234567890123")
    plaintext = "sk-same-value"

    c1 = svc.encrypt(plaintext)
    c2 = svc.encrypt(plaintext)
    assert c1 != c2


def test_decrypt_tampered_data_raises():
    svc = EncryptionService(key_bytes=b"test-key-12345678901234567890123")
    encrypted = svc.encrypt("my-key")

    with pytest.raises(ValueError):
        svc.decrypt(encrypted + "tampered")


def test_extract_key_prefix():
    assert EncryptionService.extract_prefix("sk-proj-abc") == "sk-"
    assert EncryptionService.extract_prefix("ant-api03-xyz") == "ant-"
    assert EncryptionService.extract_prefix("ak-123456") == "ak-"


def test_extract_last_4():
    assert EncryptionService.extract_last_4("sk-proj-abc123xyz4567abcd") == "abcd"
    assert EncryptionService.extract_last_4("short") == "hort"


def test_mask_key():
    svc = EncryptionService(key_bytes=b"test-key-12345678901234567890123")
    masked = svc.mask_key("sk-", "abcd")
    assert masked == "sk-...****abcd"
