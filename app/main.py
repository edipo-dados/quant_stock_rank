"""
Aplicação FastAPI principal.

Entry point da API REST do sistema de ranking quantitativo.

Valida: Requisitos 6.7, 6.8
"""

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError
import logging
import sys

from app.api.routes import router
from app.config import settings
from app.core.exceptions import QuantRankerException

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

# Criar aplicação FastAPI
app = FastAPI(
    title="Quant Stock Ranker API",
    description="API REST para sistema de ranking quantitativo de ações",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Incluir rotas
app.include_router(router, prefix="/api/v1", tags=["ranking"])


@app.exception_handler(QuantRankerException)
async def quant_ranker_exception_handler(request: Request, exc: QuantRankerException):
    """
    Handler para exceções customizadas do sistema.
    
    Args:
        request: Request FastAPI
        exc: Exceção customizada
        
    Returns:
        JSONResponse com erro 500
        
    Valida: Requisito 6.7
    """
    logger.error(f"QuantRankerException: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": f"Erro interno: {str(exc)}"}
    )


@app.exception_handler(SQLAlchemyError)
async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError):
    """
    Handler para erros de banco de dados.
    
    Args:
        request: Request FastAPI
        exc: Exceção SQLAlchemy
        
    Returns:
        JSONResponse com erro 500
        
    Valida: Requisito 6.7
    """
    logger.error(f"Database error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Erro ao acessar banco de dados"}
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Handler para erros de validação de request.
    
    Args:
        request: Request FastAPI
        exc: Exceção de validação
        
    Returns:
        JSONResponse com erro 422
        
    Valida: Requisito 6.7
    """
    logger.warning(f"Validation error: {exc}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": exc.errors()}
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """
    Handler genérico para exceções não tratadas.
    
    Args:
        request: Request FastAPI
        exc: Exceção genérica
        
    Returns:
        JSONResponse com erro 500
        
    Valida: Requisito 6.7
    """
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Erro interno do servidor"}
    )


@app.get("/health", tags=["health"])
async def health_check():
    """
    Endpoint de health check.
    
    Returns:
        Dict com status da aplicação
    """
    return {"status": "healthy", "version": "1.0.0"}


@app.on_event("startup")
async def startup_event():
    """
    Evento executado no startup da aplicação.
    
    Valida: Requisito 6.8
    """
    logger.info("Starting Quant Stock Ranker API")
    logger.info(f"API Host: {settings.api_host}")
    logger.info(f"API Port: {settings.api_port}")
    logger.info(f"Log Level: {settings.log_level}")


@app.on_event("shutdown")
async def shutdown_event():
    """
    Evento executado no shutdown da aplicação.
    
    Valida: Requisito 6.8
    """
    logger.info("Shutting down Quant Stock Ranker API")


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=True,
        log_level=settings.log_level.lower()
    )
