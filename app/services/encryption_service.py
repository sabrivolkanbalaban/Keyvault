import os
from pathlib import Path

from cryptography.fernet import Fernet, InvalidToken


class EncryptionService:
    _fernet = None

    @classmethod
    def initialize(cls, instance_path: str):
        """Load or generate the master encryption key."""
        key_path = Path(instance_path) / "encryption.key"

        if key_path.exists():
            with open(key_path, "rb") as f:
                key = f.read().strip()
        else:
            key = Fernet.generate_key()
            key_path.parent.mkdir(parents=True, exist_ok=True)
            with open(key_path, "wb") as f:
                f.write(key)
            cls._restrict_file_permissions(key_path)

        cls._fernet = Fernet(key)

    @classmethod
    def encrypt(cls, plaintext: str) -> str:
        """Encrypt a string and return base64-encoded ciphertext."""
        if not plaintext:
            return ""
        token = cls._fernet.encrypt(plaintext.encode("utf-8"))
        return token.decode("utf-8")

    @classmethod
    def decrypt(cls, ciphertext: str) -> str:
        """Decrypt a Fernet token back to plaintext."""
        if not ciphertext:
            return ""
        try:
            plaintext = cls._fernet.decrypt(ciphertext.encode("utf-8"))
            return plaintext.decode("utf-8")
        except InvalidToken:
            raise ValueError("Decryption failed: invalid token or wrong key")

    @staticmethod
    def _restrict_file_permissions(path: Path):
        """On Windows, restrict key file access using icacls."""
        if os.name == "nt":
            import subprocess

            subprocess.run(
                [
                    "icacls",
                    str(path),
                    "/inheritance:r",
                    "/grant:r",
                    f"{os.getlogin()}:(R)",
                ],
                capture_output=True,
            )
