from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from utils.config_loader import Config

# Load configuration (.env + YAML)
config = Config()

# Construct PostgreSQL Database URL
DB_URL = (
    f"postgresql://{config.get_env('POSTGRES_USER')}:"
    f"{config.get_env('POSTGRES_PASSWORD')}@"
    f"{config.get_env('POSTGRES_HOST')}:"
    f"{config.get_env('POSTGRES_PORT')}/"
    f"{config.get_env('POSTGRES_DB')}"
)

# --------------------------
# SQLAlchemy Engine
# --------------------------
# echo = True → SQL will print in console (use only for debugging)
engine = create_engine(
    DB_URL,
    echo=False,            # change to True during debugging
    pool_size=10,          # number of persistent connections
    max_overflow=20,       # extra connections allowed beyond pool_size
    pool_pre_ping=True,    # validates connection before using (avoids stale connections)
    pool_recycle=1800      # recycle connections every 30 minutes
)

# --------------------------
# Session Factory
# --------------------------
# Each request/worker should use its own session
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# --------------------------
# Base ORM Model
# --------------------------
Base = declarative_base()
