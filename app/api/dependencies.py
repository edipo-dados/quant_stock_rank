"""
Dependências FastAPI para injeção de dependências.

Fornece funções de dependência para obter sessões de banco de dados,
serviços e configurações.
"""

from typing import Generator
from sqlalchemy.orm import Session

from app.models.database import SessionLocal
from app.config import settings


def get_db() -> Generator[Session, None, None]:
    """
    Dependência para obter sessão de banco de dados.
    
    Yields:
        Session: Sessão SQLAlchemy
        
    Usage:
        @app.get("/endpoint")
        def endpoint(db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_config():
    """
    Dependência para obter configurações.
    
    Returns:
        Settings: Objeto de configurações
        
    Usage:
        @app.get("/endpoint")
        def endpoint(config: Settings = Depends(get_config)):
            ...
    """
    return settings
