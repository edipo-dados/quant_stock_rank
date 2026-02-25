"""
Serviço para persistência de features calculadas.

Valida: Requisitos 2.9, 3.7
"""

import logging
from datetime import date
from typing import Dict, List, Tuple, Any
import pandas as pd
import numpy as np

from sqlalchemy.orm import Session

from app.models.schemas import FeatureDaily, FeatureMonthly, RawPriceDaily, RawFundamental
from app.filters.eligibility_filter import EligibilityFilter
from app.config import Settings

logger = logging.getLogger(__name__)


def convert_numpy_to_python(value: Any) -> Any:
    """
    Converte valores NumPy para tipos Python nativos.
    
    Args:
        value: Valor a ser convertido
    
    Returns:
        Valor convertido para tipo Python nativo
    """
    if value is None:
        return None
    if isinstance(value, (np.integer, np.floating)):
        return float(value)
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, (np.bool_, bool)):
        return bool(value)
    return value


class FeatureService:
    """
    Serviço para salvar e recuperar features calculadas.
    
    Valida: Requisitos 2.9, 3.7
    """
    
    def __init__(self, db_session: Session, config: Settings = None):
        """
        Inicializa o serviço de features.
        
        Args:
            db_session: Sessão do banco de dados
            config: Configuração do sistema (opcional, usa settings padrão se None)
        """
        self.db = db_session
        
        # Inicializar filtro de elegibilidade
        if config is None:
            from app.config import settings
            config = settings
        self.eligibility_filter = EligibilityFilter(config)
    
    def save_daily_features(
        self,
        ticker: str,
        feature_date: date,
        features: Dict[str, float]
    ) -> FeatureDaily:
        """
        Salva features diárias (momentum) para um ativo.
        
        Args:
            ticker: Símbolo do ativo
            feature_date: Data das features
            features: Dict com chaves: return_1m, return_6m, return_12m, 
                     momentum_6m_ex_1m, momentum_12m_ex_1m, rsi_14,
                     volatility_90d, recent_drawdown
        
        Returns:
            Objeto FeatureDaily salvo
            
        Raises:
            Exception: Se houver erro ao salvar
            
        Valida: Requisito 3.7
        """
        try:
            # Converter valores NumPy para Python nativos
            features_converted = {k: convert_numpy_to_python(v) for k, v in features.items()}
            
            # Verifica se registro já existe
            existing = self.db.query(FeatureDaily).filter_by(
                ticker=ticker,
                date=feature_date
            ).first()
            
            if existing:
                # Atualiza registro existente
                existing.return_1m = features_converted.get('return_1m')
                existing.return_6m = features_converted.get('return_6m')
                existing.return_12m = features_converted.get('return_12m')
                existing.momentum_6m_ex_1m = features_converted.get('momentum_6m_ex_1m')
                existing.momentum_12m_ex_1m = features_converted.get('momentum_12m_ex_1m')
                existing.rsi_14 = features_converted.get('rsi_14')
                existing.volatility_90d = features_converted.get('volatility_90d')
                existing.recent_drawdown = features_converted.get('recent_drawdown')
                
                logger.info(f"Updated daily features for {ticker} on {feature_date}")
                record = existing
            else:
                # Cria novo registro
                record = FeatureDaily(
                    ticker=ticker,
                    date=feature_date,
                    return_1m=features_converted.get('return_1m'),
                    return_6m=features_converted.get('return_6m'),
                    return_12m=features_converted.get('return_12m'),
                    momentum_6m_ex_1m=features_converted.get('momentum_6m_ex_1m'),
                    momentum_12m_ex_1m=features_converted.get('momentum_12m_ex_1m'),
                    rsi_14=features_converted.get('rsi_14'),
                    volatility_90d=features_converted.get('volatility_90d'),
                    recent_drawdown=features_converted.get('recent_drawdown')
                )
                self.db.add(record)
                logger.info(f"Created daily features for {ticker} on {feature_date}")
            
            # Commit
            self.db.commit()
            self.db.refresh(record)
            
            return record
            
        except Exception as e:
            logger.error(f"Error saving daily features for {ticker}: {e}")
            self.db.rollback()
            raise
    
    def save_monthly_features(
        self,
        ticker: str,
        month: date,
        features: Dict[str, float]
    ) -> FeatureMonthly:
        """
        Salva features mensais (fundamentalistas) para um ativo.
        
        Args:
            ticker: Símbolo do ativo
            month: Primeiro dia do mês das features
            features: Dict com chaves: roe, net_margin, revenue_growth_3y,
                     debt_to_ebitda, pe_ratio, ev_ebitda, pb_ratio
        
        Returns:
            Objeto FeatureMonthly salvo
            
        Raises:
            Exception: Se houver erro ao salvar
            
        Valida: Requisito 2.9
        """
        try:
            # Converter valores NumPy para Python nativos
            features_converted = {k: convert_numpy_to_python(v) for k, v in features.items()}
            
            # Verifica se registro já existe
            existing = self.db.query(FeatureMonthly).filter_by(
                ticker=ticker,
                month=month
            ).first()
            
            if existing:
                # Atualiza registro existente
                existing.roe = features_converted.get('roe')
                existing.net_margin = features_converted.get('net_margin')
                existing.revenue_growth_3y = features_converted.get('revenue_growth_3y')
                existing.debt_to_ebitda = features_converted.get('debt_to_ebitda')
                existing.pe_ratio = features_converted.get('pe_ratio')
                existing.ev_ebitda = features_converted.get('ev_ebitda')
                existing.pb_ratio = features_converted.get('pb_ratio')
                existing.price_to_book = features_converted.get('price_to_book')
                existing.fcf_yield = features_converted.get('fcf_yield')
                existing.size_factor = features_converted.get('size_factor')
                existing.roe_mean_3y = features_converted.get('roe_mean_3y')
                existing.roe_volatility = features_converted.get('roe_volatility')
                existing.debt_to_ebitda_raw = features_converted.get('debt_to_ebitda_raw')
                existing.net_income_last_year = features_converted.get('net_income_last_year')
                existing.net_income_history = features_converted.get('net_income_history')
                
                logger.info(f"Updated monthly features for {ticker} on {month}")
                record = existing
            else:
                # Cria novo registro
                record = FeatureMonthly(
                    ticker=ticker,
                    month=month,
                    roe=features_converted.get('roe'),
                    net_margin=features_converted.get('net_margin'),
                    revenue_growth_3y=features_converted.get('revenue_growth_3y'),
                    debt_to_ebitda=features_converted.get('debt_to_ebitda'),
                    pe_ratio=features_converted.get('pe_ratio'),
                    ev_ebitda=features_converted.get('ev_ebitda'),
                    pb_ratio=features_converted.get('pb_ratio'),
                    price_to_book=features_converted.get('price_to_book'),
                    fcf_yield=features_converted.get('fcf_yield'),
                    size_factor=features_converted.get('size_factor'),
                    roe_mean_3y=features_converted.get('roe_mean_3y'),
                    roe_volatility=features_converted.get('roe_volatility'),
                    debt_to_ebitda_raw=features_converted.get('debt_to_ebitda_raw'),
                    net_income_last_year=features_converted.get('net_income_last_year'),
                    net_income_history=features_converted.get('net_income_history')
                )
                self.db.add(record)
                logger.info(f"Created monthly features for {ticker} on {month}")
            
            # Commit
            self.db.commit()
            self.db.refresh(record)
            
            return record
            
        except Exception as e:
            logger.error(f"Error saving monthly features for {ticker}: {e}")
            self.db.rollback()
            raise
    
    def save_batch_daily_features(
        self,
        features_list: List[Dict]
    ) -> Dict[str, any]:
        """
        Salva múltiplas features diárias em batch.
        
        Args:
            features_list: Lista de dicts, cada um contendo:
                          - ticker: str
                          - date: date
                          - features: Dict[str, float]
        
        Returns:
            Dict com estatísticas:
            {
                "success": [lista de tickers com sucesso],
                "failed": [lista de dicts com ticker e erro],
                "total_records": número total de registros inseridos
            }
        """
        results = {
            "success": [],
            "failed": [],
            "total_records": 0
        }
        
        for item in features_list:
            try:
                ticker = item['ticker']
                feature_date = item['date']
                features = item['features']
                
                self.save_daily_features(ticker, feature_date, features)
                
                results["success"].append(ticker)
                results["total_records"] += 1
                
            except Exception as e:
                ticker = item.get('ticker', 'unknown')
                logger.error(f"Failed to save daily features for {ticker}: {e}")
                results["failed"].append({"ticker": ticker, "error": str(e)})
                continue
        
        logger.info(
            f"Batch daily features save complete: {len(results['success'])} succeeded, "
            f"{len(results['failed'])} failed"
        )
        
        return results
    
    def save_batch_monthly_features(
        self,
        features_list: List[Dict]
    ) -> Dict[str, any]:
        """
        Salva múltiplas features mensais em batch.
        
        Args:
            features_list: Lista de dicts, cada um contendo:
                          - ticker: str
                          - month: date
                          - features: Dict[str, float]
        
        Returns:
            Dict com estatísticas:
            {
                "success": [lista de tickers com sucesso],
                "failed": [lista de dicts com ticker e erro],
                "total_records": número total de registros inseridos
            }
        """
        results = {
            "success": [],
            "failed": [],
            "total_records": 0
        }
        
        for item in features_list:
            try:
                ticker = item['ticker']
                month = item['month']
                features = item['features']
                
                self.save_monthly_features(ticker, month, features)
                
                results["success"].append(ticker)
                results["total_records"] += 1
                
            except Exception as e:
                ticker = item.get('ticker', 'unknown')
                logger.error(f"Failed to save monthly features for {ticker}: {e}")
                results["failed"].append({"ticker": ticker, "error": str(e)})
                continue
        
        logger.info(
            f"Batch monthly features save complete: {len(results['success'])} succeeded, "
            f"{len(results['failed'])} failed"
        )
        
        return results
    
    def get_daily_features(
        self,
        ticker: str,
        feature_date: date
    ) -> FeatureDaily:
        """
        Recupera features diárias para um ativo em uma data específica.
        
        Args:
            ticker: Símbolo do ativo
            feature_date: Data das features
        
        Returns:
            Objeto FeatureDaily ou None se não encontrado
        """
        return self.db.query(FeatureDaily).filter_by(
            ticker=ticker,
            date=feature_date
        ).first()
    
    def get_monthly_features(
        self,
        ticker: str,
        month: date
    ) -> FeatureMonthly:
        """
        Recupera features mensais para um ativo em um mês específico.
        
        Args:
            ticker: Símbolo do ativo
            month: Primeiro dia do mês
        
        Returns:
            Objeto FeatureMonthly ou None se não encontrado
        """
        return self.db.query(FeatureMonthly).filter_by(
            ticker=ticker,
            month=month
        ).first()
    
    def get_all_daily_features_for_date(
        self,
        feature_date: date
    ) -> List[FeatureDaily]:
        """
        Recupera features diárias de todos os ativos para uma data específica.
        
        Args:
            feature_date: Data das features
        
        Returns:
            Lista de objetos FeatureDaily
        """
        return self.db.query(FeatureDaily).filter_by(
            date=feature_date
        ).all()
    
    def get_all_monthly_features_for_month(
        self,
        month: date
    ) -> List[FeatureMonthly]:
        """
        Recupera features mensais de todos os ativos para um mês específico.
        
        Args:
            month: Primeiro dia do mês
        
        Returns:
            Lista de objetos FeatureMonthly
        """
        return self.db.query(FeatureMonthly).filter_by(
            month=month
        ).all()
    
    def filter_eligible_assets(
        self,
        tickers: List[str],
        reference_date: date
    ) -> Tuple[List[str], Dict[str, List[str]]]:
        """
        Filtra ativos elegíveis antes do cálculo de fatores.
        
        Este método aplica o filtro de elegibilidade para excluir ativos
        financeiramente distressed antes da normalização e scoring.
        
        Args:
            tickers: Lista de símbolos de ativos a filtrar
            reference_date: Data de referência para buscar dados
        
        Returns:
            Tupla de (eligible_tickers, exclusion_reasons)
            - eligible_tickers: Lista de tickers que passaram no filtro
            - exclusion_reasons: Dict mapeando tickers excluídos para suas razões
        
        Valida: Requisitos 1.1, 1.6
        """
        logger.info(f"Filtering {len(tickers)} assets for eligibility on {reference_date}")
        
        assets_data = {}
        
        for ticker in tickers:
            try:
                # Buscar dados fundamentalistas mais recentes
                fundamentals_query = self.db.query(RawFundamental).filter(
                    RawFundamental.ticker == ticker,
                    RawFundamental.period_end_date <= reference_date
                ).order_by(RawFundamental.period_end_date.desc()).first()
                
                if not fundamentals_query:
                    logger.warning(f"No fundamental data found for {ticker}")
                    assets_data[ticker] = {
                        'fundamentals': None,
                        'volume_data': None
                    }
                    continue
                
                # Extrair dados fundamentalistas
                fundamentals = {
                    'shareholders_equity': fundamentals_query.shareholders_equity,
                    'ebitda': fundamentals_query.ebitda,
                    'revenue': fundamentals_query.revenue,
                    'net_income_last_year': fundamentals_query.net_income,
                    'net_debt_to_ebitda': fundamentals_query.total_debt / fundamentals_query.ebitda if (
                        fundamentals_query.total_debt is not None and 
                        fundamentals_query.ebitda is not None and 
                        fundamentals_query.ebitda != 0
                    ) else None
                }
                
                # Buscar histórico de lucro líquido dos últimos 3 anos
                net_income_history_query = self.db.query(RawFundamental).filter(
                    RawFundamental.ticker == ticker,
                    RawFundamental.period_end_date <= reference_date
                ).order_by(RawFundamental.period_end_date.desc()).limit(3).all()
                
                fundamentals['net_income_history'] = [
                    f.net_income for f in net_income_history_query if f.net_income is not None
                ]
                
                # Buscar dados de volume (últimos 90 dias)
                volume_query = self.db.query(RawPriceDaily).filter(
                    RawPriceDaily.ticker == ticker,
                    RawPriceDaily.date <= reference_date
                ).order_by(RawPriceDaily.date.desc()).limit(90).all()
                
                if not volume_query:
                    logger.warning(f"No volume data found for {ticker}")
                    volume_data = None
                else:
                    volume_data = pd.DataFrame([
                        {'date': p.date, 'volume': p.volume}
                        for p in volume_query
                    ])
                
                assets_data[ticker] = {
                    'fundamentals': fundamentals,
                    'volume_data': volume_data
                }
                
            except Exception as e:
                logger.error(f"Error gathering data for {ticker}: {e}")
                assets_data[ticker] = {
                    'fundamentals': None,
                    'volume_data': None
                }
                continue
        
        # Aplicar filtro de elegibilidade
        eligible_tickers, exclusion_reasons = self.eligibility_filter.filter_universe(assets_data)
        
        logger.info(
            f"Eligibility filter results: {len(eligible_tickers)} eligible, "
            f"{len(exclusion_reasons)} excluded"
        )
        
        # Log exclusion reasons
        for ticker, reasons in exclusion_reasons.items():
            logger.debug(f"Excluded {ticker}: {', '.join(reasons)}")
        
        return eligible_tickers, exclusion_reasons
