import datetime
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, Text
from sqlalchemy.orm import declarative_base, sessionmaker, scoped_session
from config import Config
import logging

logger = logging.getLogger(__name__)
Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(120), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), default="member") # member or admin
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    last_login = Column(DateTime, nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "role": self.role,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_login": self.last_login.isoformat() if self.last_login else None
        }

class SessionLog(Base):
    __tablename__ = "session_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False, index=True)
    username = Column(String(50), nullable=False)
    event_type = Column(String(50), nullable=False) # LOGIN, LOGOUT, REGISTER, REFRESH, FAILED_LOGIN
    ip_address = Column(String(50), default="127.0.0.1")
    user_agent = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "username": self.username,
            "event_type": self.event_type,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }

engine = None
SessionLocal = None
active_db_engine = "unknown"

def init_db():
    global engine, SessionLocal, active_db_engine
    
    # Try PostgreSQL first if requested or configured
    chosen_uri = Config.SQLITE_URI
    active_db_engine = "SQLite"

    if Config.USE_POSTGRES in ["true", "1", "auto"]:
        try:
            logger.info("Testing PostgreSQL connection: %s", Config.POSTGRES_URI)
            pg_engine = create_engine(Config.POSTGRES_URI, pool_pre_ping=True, connect_args={"connect_timeout": 3})
            with pg_engine.connect() as conn:
                logger.info("Successfully connected to PostgreSQL server!")
            chosen_uri = Config.POSTGRES_URI
            active_db_engine = "PostgreSQL"
        except Exception as e:
            logger.warning(f"PostgreSQL connection unavailable ({e}). Falling back smoothly to local SQLite database.")
            chosen_uri = Config.SQLITE_URI
            active_db_engine = "SQLite (Failover/Standalone)"

    engine = create_engine(chosen_uri, pool_pre_ping=True)
    Base.metadata.create_all(bind=engine)
    SessionLocal = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))
    logger.info(f"Database initialized using engine: {active_db_engine}")
    return engine

def get_db():
    if SessionLocal is None:
        init_db()
    db = SessionLocal()
    try:
        return db
    finally:
        pass
