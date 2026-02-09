from app.services.encryption_service import EncryptionService


def test_encrypt_decrypt(app):
    """Test basic encrypt/decrypt cycle."""
    with app.app_context():
        plaintext = "SuperSecretPassword123!"
        encrypted = EncryptionService.encrypt(plaintext)

        assert encrypted != plaintext
        assert len(encrypted) > 0

        decrypted = EncryptionService.decrypt(encrypted)
        assert decrypted == plaintext


def test_encrypt_empty_string(app):
    """Test encrypting empty string returns empty."""
    with app.app_context():
        assert EncryptionService.encrypt("") == ""
        assert EncryptionService.decrypt("") == ""


def test_encrypt_unicode(app):
    """Test encrypting unicode characters."""
    with app.app_context():
        plaintext = "Türkçe şifre: güçlü parola"
        encrypted = EncryptionService.encrypt(plaintext)
        decrypted = EncryptionService.decrypt(encrypted)
        assert decrypted == plaintext


def test_different_plaintexts_different_ciphertexts(app):
    """Test that same plaintext produces different ciphertext each time."""
    with app.app_context():
        plaintext = "test"
        enc1 = EncryptionService.encrypt(plaintext)
        enc2 = EncryptionService.encrypt(plaintext)
        # Fernet includes a timestamp, so same input produces different output
        assert enc1 != enc2
        # But both decrypt to the same value
        assert EncryptionService.decrypt(enc1) == plaintext
        assert EncryptionService.decrypt(enc2) == plaintext
