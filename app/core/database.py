from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

# Render fournit DATABASE_URL avec "postgres://" (ancien format)
# SQLAlchemy 2.x exige "postgresql://"
db_url = settings.DATABASE_URL
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)
    logger.info("DATABASE_URL corrigé : postgres:// → postgresql://")

engine = create_engine(
    db_url,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
    pool_recycle=300,   # Recycle les connexions toutes les 5 min (Render idle)
    echo=settings.DEBUG,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """Dépendance FastAPI — session de base de données."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
