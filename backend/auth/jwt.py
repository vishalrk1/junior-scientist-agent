import jwt
from typing import Optional, Dict, Any
from datetime import datetime
from config import settings

def verify_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Verify a JWT token and return the decoded payload if valid.
    Returns None if token is invalid.
    """
    try:
        # Decode and verify the token
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        
        # Check if token has expired
        exp = payload.get('exp')
        if exp and datetime.utcnow().timestamp() > exp:
            return None
            
        return {
            "id": payload.get("id"),
            "email": payload.get("sub"),
            "name": payload.get("name"),
            "exp": payload.get("exp")
        }
    except jwt.InvalidTokenError:
        return None
