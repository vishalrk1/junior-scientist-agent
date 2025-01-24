from datetime import datetime, timedelta
from passlib.context import CryptContext
import jwt 
from config import settings
import string
import secrets

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password: str) -> str:
    """Hashes a plain-text password."""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plain-text password against a hashed password."""
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict, expires_delta: timedelta = None) -> str:
    """
    Creates a JSON Web Token (JWT) with an expiration time.

    Args:
        data (dict): Data to encode in the token.
        expires_delta (timedelta, optional): Expiration time delta. Defaults to config settings.

    Returns:
        str: Encoded JWT.
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

def generate_reset_token(length: int = 32) -> str:
    """
    Generates a random reset token using alphanumeric characters.

    Args:
        length (int, optional): Length of the token. Defaults to 32.

    Returns:
        str: Randomly generated token.
    """
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))
