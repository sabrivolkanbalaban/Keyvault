import string

from app.services.password_generator import PasswordGenerator


def test_generate_default_length():
    password = PasswordGenerator.generate()
    assert len(password) == 20


def test_generate_custom_length():
    password = PasswordGenerator.generate(length=32)
    assert len(password) == 32


def test_generate_contains_required_chars():
    password = PasswordGenerator.generate(length=20)
    assert any(c.isupper() for c in password)
    assert any(c.islower() for c in password)
    assert any(c.isdigit() for c in password)


def test_generate_no_symbols():
    password = PasswordGenerator.generate(length=20, use_symbols=False)
    assert all(c not in "!@#$%^&*()-_=+[]{}|;:,.<>?" for c in password)


def test_generate_only_digits():
    password = PasswordGenerator.generate(
        length=10, use_uppercase=False, use_lowercase=False,
        use_digits=True, use_symbols=False
    )
    assert all(c.isdigit() for c in password)


def test_strength_weak():
    result = PasswordGenerator.calculate_strength("abc")
    assert result["strength"] == "weak"


def test_strength_strong():
    result = PasswordGenerator.calculate_strength("MyStr0ng!Password123")
    assert result["strength"] == "strong"
