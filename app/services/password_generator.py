import secrets
import string


class PasswordGenerator:
    @staticmethod
    def generate(
        length: int = 20,
        use_uppercase: bool = True,
        use_lowercase: bool = True,
        use_digits: bool = True,
        use_symbols: bool = True,
        exclude_ambiguous: bool = True,
        custom_symbols: str = "!@#$%^&*()-_=+[]{}|;:,.<>?",
    ) -> str:
        chars = ""
        required = []

        if use_lowercase:
            pool = string.ascii_lowercase
            if exclude_ambiguous:
                pool = pool.replace("l", "")
            chars += pool
            required.append(secrets.choice(pool))

        if use_uppercase:
            pool = string.ascii_uppercase
            if exclude_ambiguous:
                pool = pool.replace("O", "").replace("I", "")
            chars += pool
            required.append(secrets.choice(pool))

        if use_digits:
            pool = string.digits
            if exclude_ambiguous:
                pool = pool.replace("0", "").replace("1", "")
            chars += pool
            required.append(secrets.choice(pool))

        if use_symbols:
            chars += custom_symbols
            required.append(secrets.choice(custom_symbols))

        if not chars:
            raise ValueError("At least one character set must be enabled")

        remaining = length - len(required)
        if remaining < 0:
            remaining = 0
            required = required[:length]

        password_chars = required + [
            secrets.choice(chars) for _ in range(remaining)
        ]

        rng = secrets.SystemRandom()
        rng.shuffle(password_chars)

        return "".join(password_chars)

    @staticmethod
    def calculate_strength(password: str) -> dict:
        score = 0
        feedback = []

        if len(password) >= 16:
            score += 30
        elif len(password) >= 12:
            score += 25
        elif len(password) >= 8:
            score += 10
        else:
            feedback.append("Too short (minimum 8 characters)")

        if any(c.isupper() for c in password):
            score += 20
        else:
            feedback.append("Add uppercase letters")

        if any(c.islower() for c in password):
            score += 10

        if any(c.isdigit() for c in password):
            score += 20
        else:
            feedback.append("Add numbers")

        if any(c in string.punctuation for c in password):
            score += 20
        else:
            feedback.append("Add symbols")

        strength = (
            "weak" if score < 40 else "medium" if score < 70 else "strong"
        )

        return {"score": score, "strength": strength, "feedback": feedback}
