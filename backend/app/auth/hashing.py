import bcrypt


def hash_password(password: str) -> str:
    encoded = password.encode("utf-8")
    if not 8 <= len(encoded) <= 72:
        raise ValueError("Password must contain 8 to 72 UTF-8 bytes.")
    return bcrypt.hashpw(encoded, bcrypt.gensalt()).decode("ascii")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    encoded = plain_password.encode("utf-8")
    if len(encoded) > 72:
        return False
    try:
        return bcrypt.checkpw(encoded, hashed_password.encode("ascii"))
    except (ValueError, UnicodeError):
        return False
