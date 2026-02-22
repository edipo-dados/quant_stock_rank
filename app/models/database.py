"""
Configuração do banco de dados SQLAlchemy.

Valida: Requisitos 8.1-8.8, 13.4, 13.7
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config import settings

# Configuração específica para SQLite vs PostgreSQL
if settings.database_url.startswith("sqlite"):
    # SQLite não suporta pool_size e max_overflow
    engine = create_engine(
        settings.database_url,
        connect_args={"check_same_thread": False}  # Necessário para SQLite
    )
else:
    # PostgreSQL e outros bancos suportam pooling
    engine = create_engine(
        settings.database_url,
        pool_pre_ping=True,  # Verifica conexões antes de usar
        pool_size=5,
        max_overflow=10
    )

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class para modelos
Base = declarative_base()


def get_db():
    """
    Dependency para obter sessão do banco de dados.
    
    Uso em FastAPI:
        @app.get("/endpoint")
        def endpoint(db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
