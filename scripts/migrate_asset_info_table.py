#!/usr/bin/env python3
"""
Script para migrar o banco de dados adicionando a tabela AssetInfo.

Esta tabela armazena informações de setor e indústria dos ativos.
"""

import sys
import os
from pathlib import Path

# Adicionar o diretório raiz ao path
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

from sqlalchemy import create_engine, text
from app.config import settings
from app.models.database import Base
from app.models.schemas import AssetInfo
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def migrate_database():
    """
    Adiciona a tabela AssetInfo ao banco de dados existente.
    """
    try:
        # Conectar ao banco
        engine = create_engine(settings.database_url)
        
        logger.info("Conectando ao banco de dados...")
        
        # Verificar se a tabela já existe
        with engine.connect() as conn:
            result = conn.execute(text(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='asset_info'"
            ))
            if result.fetchone():
                logger.info("Tabela asset_info já existe, pulando migração")
                return
        
        logger.info("Criando tabela asset_info...")
        
        # Criar apenas a tabela AssetInfo
        AssetInfo.__table__.create(engine, checkfirst=True)
        
        logger.info("Migração concluída com sucesso!")
        logger.info("Tabela asset_info criada")
        
        # Verificar se foi criada
        with engine.connect() as conn:
            result = conn.execute(text(
                "SELECT sql FROM sqlite_master WHERE type='table' AND name='asset_info'"
            ))
            table_sql = result.fetchone()
            if table_sql:
                logger.info("Estrutura da tabela:")
                logger.info(table_sql[0])
            else:
                logger.error("Erro: Tabela não foi criada")
                return False
        
        return True
        
    except Exception as e:
        logger.error(f"Erro durante a migração: {e}")
        return False


if __name__ == "__main__":
    success = migrate_database()
    if success:
        print("\n✅ Migração concluída com sucesso!")
        print("A tabela asset_info foi adicionada ao banco de dados.")
        print("\nPróximos passos:")
        print("1. Execute o pipeline para popular automaticamente as informações de setor")
        print("2. Ou use o AssetInfoService para buscar informações específicas")
    else:
        print("\n❌ Erro durante a migração")
        sys.exit(1)