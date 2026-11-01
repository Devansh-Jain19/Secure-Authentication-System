import bcrypt
import jwt
import datetime
from functools import wraps
from flask import request, jsonify
from config import Config

def hash_password(plain_password: str) -> str:
    """Secure password hashing using bcrypt with high work factor salt."""
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(plain_password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against stored bcrypt hash."""
    try:
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
    except Exception:
        return False

def generate_tokens(user_id: int, username: str, role: str):
    """Generate both short-lived Access Token and Refresh Token with JWT."""
    now = datetime.datetime.utcnow()
    
    # Access token payload (sub must be string according to RFC 7519 / PyJWT standard)
    access_payload = {
        "sub": str(user_id),
        "username": username,
        "role": role,
        "type": "access",
        "iat": now,
        "exp": now + Config.JWT_ACCESS_TOKEN_EXPIRES
    }
    
    # Refresh token payload (valid for 7 days)
    refresh_payload = {
        "sub": str(user_id),
        "username": username,
        "role": role,
        "type": "refresh",
        "iat": now,
        "exp": now + datetime.timedelta(days=7)
    }
    
    access_token = jwt.encode(access_payload, Config.JWT_SECRET_KEY, algorithm=Config.JWT_ALGORITHM)
    refresh_token = jwt.encode(refresh_payload, Config.JWT_SECRET_KEY, algorithm=Config.JWT_ALGORITHM)
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "Bearer",
        "expires_in": int(Config.JWT_ACCESS_TOKEN_EXPIRES.total_seconds())
    }

def decode_token(token: str):
    """Decode and validate JWT signature and expiration."""
    try:
        payload = jwt.decode(token, Config.JWT_SECRET_KEY, algorithms=[Config.JWT_ALGORITHM])
        return payload, None
    except jwt.ExpiredSignatureError:
        return None, "Token has expired. Please log in again."
    except jwt.InvalidTokenError:
        return None, "Invalid authentication token."

def token_required(f):
    """Decorator to enforce secure JWT authentication on protected routes."""
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization", None)
        if not auth_header:
            return jsonify({"status": "error", "message": "Missing Authorization header."}), 401
            
        parts = auth_header.split()
        if len(parts) != 2 or parts[0].lower() != "bearer":
            return jsonify({"status": "error", "message": "Invalid token header format. Format must be 'Bearer <token>'."}), 401
            
        token = parts[1]
        payload, err = decode_token(token)
        if err or not payload:
            return jsonify({"status": "error", "message": err}), 401
            
        if payload.get("type") != "access":
            return jsonify({"status": "error", "message": "Access token required for this operation."}), 401
            
        request.current_user = payload
        return f(*args, **kwargs)
    return decorated
