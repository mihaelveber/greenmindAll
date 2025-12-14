import jwt
from datetime import datetime, timedelta
from typing import Optional
from django.conf import settings
from django.contrib.auth import get_user_model
from ninja.security import HttpBearer

User = get_user_model()

class JWTAuth(HttpBearer):
    async def authenticate(self, request, token):
        try:
            payload = jwt.decode(
                token,
                settings.JWT_SECRET_KEY,
                algorithms=[settings.JWT_ALGORITHM]
            )
            user_id = payload.get('user_id')
            if user_id is None:
                return None
            
            user = await User.objects.aget(id=user_id)
            return user
        except (jwt.DecodeError, jwt.ExpiredSignatureError, User.DoesNotExist):
            return None

def create_access_token(user_id: int) -> str:
    """Ustvari JWT access token"""
    payload = {
        'user_id': user_id,
        'exp': datetime.utcnow() + timedelta(seconds=settings.JWT_ACCESS_TOKEN_LIFETIME),
        'iat': datetime.utcnow(),
        'type': 'access'
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

def create_refresh_token(user_id: int) -> str:
    """Ustvari JWT refresh token"""
    payload = {
        'user_id': user_id,
        'exp': datetime.utcnow() + timedelta(seconds=settings.JWT_REFRESH_TOKEN_LIFETIME),
        'iat': datetime.utcnow(),
        'type': 'refresh'
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

def verify_refresh_token(token: str) -> Optional[int]:
    """Preveri refresh token in vrne user_id"""
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        if payload.get('type') != 'refresh':
            return None
        return payload.get('user_id')
    except (jwt.DecodeError, jwt.ExpiredSignatureError):
        return None
