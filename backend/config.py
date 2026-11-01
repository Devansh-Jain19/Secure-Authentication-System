import os
from datetime import timedelta

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "super-secret-production-grade-jwt-key-2026")
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "secure-jwt-signing-key-998877665544")
    JWT_ALGORITHM = "HS256"
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=int(os.getenv("JWT_ACCESS_EXPIRE_HOURS", 2)))
    
    # Database Configuration: Supports PostgreSQL and falls back gracefully to SQLite
    # Example PostgreSQL URI: postgresql://postgres:postgres@localhost:5432/secure_auth_db
    DB_USER = os.getenv("DB_USER", "postgres")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = os.getenv("DB_PORT", "5432")
    DB_NAME = os.getenv("DB_NAME", "secure_auth_db")
    
    # Priority: DB_URI -> PostgreSQL default -> SQLite local storage
    USE_POSTGRES = os.getenv("USE_POSTGRES", "auto").lower()
    POSTGRES_URI = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    SQLITE_URI = f"sqlite:///{os.path.join(BASE_DIR, 'auth_database.sqlite3')}"
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
