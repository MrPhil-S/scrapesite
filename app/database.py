from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from .my_secrets import dev_sql_alchemy

# Database connection URL
SQLALCHEMY_DATABASE_URL = dev_sql_alchemy
# Create engine
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"charset": "utf8mb4"})

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()

# Dependency function to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()