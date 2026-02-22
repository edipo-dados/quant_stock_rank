"""
Serviço para buscar e armazenar informações de ativos (setor, indústria, etc).
"""

import logging
from typing import Dict, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
import yfinance as yf

from app.models.schemas import AssetInfo
from app.core.exceptions import DataFetchError

logger = logging.getLogger(__name__)


class AssetInfoService:
    """
    Serviço para gerenciar informações básicas dos ativos.
    """
    
    def __init__(self, db: Session):
        """
        Inicializa o serviço.
        
        Args:
            db: Sessão do banco de dados
        """
        self.db = db
    
    def get_asset_info(self, ticker: str) -> Optional[AssetInfo]:
        """
        Busca informações do ativo no banco de dados.
        
        Args:
            ticker: Símbolo do ativo
            
        Returns:
            AssetInfo se encontrado, None caso contrário
        """
        return self.db.query(AssetInfo).filter(AssetInfo.ticker == ticker).first()
    
    def fetch_and_store_asset_info(self, ticker: str, force_update: bool = False) -> AssetInfo:
        """
        Busca informações do ativo no Yahoo Finance e armazena no banco.
        
        Args:
            ticker: Símbolo do ativo
            force_update: Se True, força atualização mesmo se já existe
            
        Returns:
            AssetInfo com as informações atualizadas
            
        Raises:
            DataFetchError: Se não conseguir buscar as informações
        """
        # Verificar se já existe e se precisa atualizar
        existing = self.get_asset_info(ticker)
        
        if existing and not force_update:
            # Verificar se foi atualizado recentemente (últimos 30 dias)
            if existing.last_updated and (datetime.utcnow() - existing.last_updated).days < 30:
                logger.debug(f"Asset info for {ticker} is recent, skipping update")
                return existing
        
        try:
            logger.info(f"Fetching asset info for {ticker}")
            
            # Buscar informações do Yahoo Finance
            stock = yf.Ticker(ticker)
            info = stock.info
            
            if not info:
                raise DataFetchError(f"No asset info data for {ticker}")
            
            # Extrair informações relevantes
            asset_data = {
                'ticker': ticker,
                'sector': info.get('sector'),
                'industry': info.get('industry'),
                'sector_key': info.get('sectorKey'),
                'industry_key': info.get('industryKey'),
                'company_name': info.get('longName') or info.get('shortName'),
                'country': info.get('country'),
                'currency': info.get('currency'),
                'last_updated': datetime.utcnow()
            }
            
            if existing:
                # Atualizar registro existente
                for key, value in asset_data.items():
                    if key != 'ticker':  # Não atualizar a chave primária
                        setattr(existing, key, value)
                asset_info = existing
            else:
                # Criar novo registro
                asset_info = AssetInfo(**asset_data)
                self.db.add(asset_info)
            
            self.db.commit()
            
            logger.info(
                f"Successfully stored asset info for {ticker}: "
                f"sector={asset_info.sector}, industry={asset_info.industry}"
            )
            
            return asset_info
            
        except DataFetchError:
            raise
        except Exception as e:
            self.db.rollback()
            error_msg = f"Failed to fetch asset info for {ticker}: {str(e)}"
            logger.error(error_msg)
            raise DataFetchError(error_msg) from e
    
    def is_financial_sector(self, ticker: str) -> bool:
        """
        Verifica se o ativo pertence ao setor financeiro.
        
        Args:
            ticker: Símbolo do ativo
            
        Returns:
            True se for do setor financeiro, False caso contrário
        """
        asset_info = self.get_asset_info(ticker)
        
        if not asset_info or not asset_info.sector:
            # Se não temos informação de setor, tentar buscar
            try:
                asset_info = self.fetch_and_store_asset_info(ticker)
            except DataFetchError:
                logger.warning(f"Could not determine sector for {ticker}, assuming non-financial")
                return False
        
        # Verificar se é setor financeiro
        financial_sectors = [
            'Financial Services',
            'Financial',
            'Banks',
            'Insurance',
            'Real Estate'
        ]
        
        if asset_info.sector:
            return any(fs.lower() in asset_info.sector.lower() for fs in financial_sectors)
        
        return False
    
    def get_sector_info(self, ticker: str) -> Dict[str, Optional[str]]:
        """
        Retorna informações de setor e indústria do ativo.
        
        Args:
            ticker: Símbolo do ativo
            
        Returns:
            Dict com sector, industry, sector_key, industry_key
        """
        asset_info = self.get_asset_info(ticker)
        
        if not asset_info:
            try:
                asset_info = self.fetch_and_store_asset_info(ticker)
            except DataFetchError:
                logger.warning(f"Could not fetch sector info for {ticker}")
                return {
                    'sector': None,
                    'industry': None,
                    'sector_key': None,
                    'industry_key': None
                }
        
        return {
            'sector': asset_info.sector,
            'industry': asset_info.industry,
            'sector_key': asset_info.sector_key,
            'industry_key': asset_info.industry_key
        }