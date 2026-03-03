"""
Módulo de validação técnica de dados.

Valida qualidade de preços e fundamentos após ingestão,
identificando problemas como buracos, outliers e dados insuficientes.
"""

import logging
from datetime import date, timedelta
from typing import List, Dict, Tuple
import pandas as pd
import numpy as np

from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.schemas import RawPriceDaily, RawFundamental

logger = logging.getLogger(__name__)


class DataValidator:
    """Valida qualidade técnica dos dados."""
    
    def __init__(self, db: Session):
        """
        Inicializa o validador.
        
        Args:
            db: Sessão do banco de dados
        """
        self.db = db
    
    def validate_prices(self, ticker: str) -> Dict:
        """
        Valida dados de preços para um ticker.
        
        Verificações:
        - Mínimo 3 anos contínuos
        - Buracos > 5 dias úteis
        - Variação diária > 40% (outliers)
        - Volume zero recorrente
        - Datas fora de ordem
        - adj_close negativo
        
        Args:
            ticker: Ticker a validar
            
        Returns:
            Dict com resultado da validação
        """
        issues = []
        warnings = []
        
        try:
            # Buscar todos os preços - usar apenas colunas necessárias
            from sqlalchemy import select
            
            stmt = select(
                RawPriceDaily.date,
                RawPriceDaily.close,
                RawPriceDaily.adj_close,
                RawPriceDaily.volume
            ).where(
                RawPriceDaily.ticker == ticker
            ).order_by(RawPriceDaily.date)
            
            result = self.db.execute(stmt).fetchall()
            
            if not result:
                return {
                    "ticker": ticker,
                    "valid": False,
                    "issues": ["No price data"],
                    "warnings": [],
                    "stats": {}
                }
            
            # Converter para DataFrame
            df = pd.DataFrame(result, columns=['date', 'close', 'adj_close', 'volume'])
            
            df['date'] = pd.to_datetime(df['date'])
            df = df.sort_values('date')
            
            # Estatísticas básicas
            min_date = df['date'].min()
            max_date = df['date'].max()
            days_span = (max_date - min_date).days
            years_span = days_span / 365.25
            
            # 1. Verificar mínimo 3 anos
            if years_span < 3.0:
                issues.append(f"Insufficient history: {years_span:.1f} years < 3 years")
            
            # 2. Verificar buracos > 5 dias úteis
            df['date_diff'] = df['date'].diff().dt.days
            large_gaps = df[df['date_diff'] > 7]  # 7 dias = ~5 dias úteis
            
            if len(large_gaps) > 0:
                warnings.append(f"Found {len(large_gaps)} gaps > 5 business days")
                for _, gap in large_gaps.head(3).iterrows():
                    warnings.append(f"  Gap of {gap['date_diff']} days ending {gap['date'].date()}")
            
            # 3. Verificar variação diária > 40%
            df['daily_return'] = df['adj_close'].pct_change()
            outliers = df[abs(df['daily_return']) > 0.40]
            
            if len(outliers) > 0:
                warnings.append(f"Found {len(outliers)} days with >40% price change")
                for _, outlier in outliers.head(3).iterrows():
                    warnings.append(
                        f"  {outlier['date'].date()}: {outlier['daily_return']*100:.1f}% change"
                    )
            
            # 4. Verificar volume zero recorrente
            zero_volume = df[df['volume'] == 0]
            zero_volume_pct = len(zero_volume) / len(df) * 100
            
            if zero_volume_pct > 10:
                warnings.append(f"High zero-volume days: {zero_volume_pct:.1f}%")
            
            # 5. Verificar datas fora de ordem (já ordenado, mas verificar duplicatas)
            duplicates = df[df['date'].duplicated()]
            if len(duplicates) > 0:
                issues.append(f"Found {len(duplicates)} duplicate dates")
            
            # 6. Verificar adj_close negativo
            negative_prices = df[df['adj_close'] < 0]
            if len(negative_prices) > 0:
                issues.append(f"Found {len(negative_prices)} negative prices")
            
            # Verificar adj_close zero
            zero_prices = df[df['adj_close'] == 0]
            if len(zero_prices) > 0:
                warnings.append(f"Found {len(zero_prices)} zero prices")
            
            # Estatísticas
            stats = {
                "min_date": min_date.date().isoformat(),
                "max_date": max_date.date().isoformat(),
                "years_span": round(years_span, 2),
                "total_days": len(df),
                "avg_volume": int(df['volume'].mean()),
                "zero_volume_pct": round(zero_volume_pct, 2),
                "outliers_count": len(outliers),
                "gaps_count": len(large_gaps)
            }
            
            # Determinar se é válido
            valid = len(issues) == 0
            
            return {
                "ticker": ticker,
                "valid": valid,
                "issues": issues,
                "warnings": warnings,
                "stats": stats
            }
            
        except Exception as e:
            logger.error(f"Erro ao validar preços de {ticker}: {e}")
            return {
                "ticker": ticker,
                "valid": False,
                "issues": [f"Validation error: {str(e)}"],
                "warnings": [],
                "stats": {}
            }
    
    def validate_fundamentals(self, ticker: str) -> Dict:
        """
        Valida dados fundamentalistas para um ticker.
        
        Verificações:
        - Mínimo 3 anos disponíveis
        - Revenue negativa
        - Equity negativa
        - EBITDA extremamente volátil (>300% variação)
        - Net income ausente
        
        Args:
            ticker: Ticker a validar
            
        Returns:
            Dict com resultado da validação
        """
        issues = []
        warnings = []
        
        try:
            # Buscar fundamentos - usar apenas colunas necessárias
            from sqlalchemy import select
            
            stmt = select(
                RawFundamental.period_end_date,
                RawFundamental.revenue,
                RawFundamental.net_income,
                RawFundamental.ebitda,
                RawFundamental.shareholders_equity,
                RawFundamental.total_debt
            ).where(
                RawFundamental.ticker == ticker,
                RawFundamental.period_type == 'annual'
            ).order_by(RawFundamental.period_end_date)
            
            result = self.db.execute(stmt).fetchall()
            
            if not result:
                return {
                    "ticker": ticker,
                    "valid": False,
                    "issues": ["No fundamental data"],
                    "warnings": [],
                    "stats": {}
                }
            
            years_available = len(result)
            
            # 1. Verificar mínimo 3 anos
            if years_available < 3:
                issues.append(f"Insufficient years: {years_available} < 3")
            
            # Converter para DataFrame para análise
            df = pd.DataFrame(
                result,
                columns=['period_end_date', 'revenue', 'net_income', 'ebitda', 'shareholders_equity', 'total_debt']
            )
            
            df = df.sort_values('period_end_date')
            
            # 2. Verificar revenue negativa
            if 'revenue' in df.columns:
                negative_revenue = df[df['revenue'] < 0]
                if len(negative_revenue) > 0:
                    issues.append(f"Found {len(negative_revenue)} periods with negative revenue")
            
            # 3. Verificar equity negativa
            if 'shareholders_equity' in df.columns:
                negative_equity = df[df['shareholders_equity'] < 0]
                if len(negative_equity) > 0:
                    issues.append(f"Found {len(negative_equity)} periods with negative equity")
            
            # 4. Verificar EBITDA extremamente volátil
            if 'ebitda' in df.columns:
                ebitda_values = df['ebitda'].dropna()
                if len(ebitda_values) >= 2:
                    ebitda_pct_change = ebitda_values.pct_change().abs()
                    extreme_volatility = ebitda_pct_change[ebitda_pct_change > 3.0]  # >300%
                    
                    if len(extreme_volatility) > 0:
                        warnings.append(
                            f"EBITDA highly volatile: {len(extreme_volatility)} periods with >300% change"
                        )
            
            # 5. Verificar net_income ausente
            if 'net_income' in df.columns:
                missing_net_income = df['net_income'].isna().sum()
                missing_pct = missing_net_income / len(df) * 100
                
                if missing_pct > 50:
                    warnings.append(f"Net income missing in {missing_pct:.0f}% of periods")
            
            # Estatísticas
            min_year = df['period_end_date'].min().year if len(df) > 0 else None
            max_year = df['period_end_date'].max().year if len(df) > 0 else None
            
            stats = {
                "years_available": years_available,
                "min_year": min_year,
                "max_year": max_year,
                "has_revenue": df['revenue'].notna().sum(),
                "has_net_income": df['net_income'].notna().sum(),
                "has_ebitda": df['ebitda'].notna().sum(),
                "has_equity": df['shareholders_equity'].notna().sum()
            }
            
            # Determinar se é válido
            valid = len(issues) == 0
            
            return {
                "ticker": ticker,
                "valid": valid,
                "issues": issues,
                "warnings": warnings,
                "stats": stats
            }
            
        except Exception as e:
            logger.error(f"Erro ao validar fundamentos de {ticker}: {e}")
            return {
                "ticker": ticker,
                "valid": False,
                "issues": [f"Validation error: {str(e)}"],
                "warnings": [],
                "stats": {}
            }
    
    def validate_all_tickers(self, tickers: List[str]) -> Dict:
        """
        Valida todos os tickers.
        
        Args:
            tickers: Lista de tickers
            
        Returns:
            Dict com relatório completo
        """
        logger.info(f"Validando {len(tickers)} tickers...")
        
        price_results = []
        fundamental_results = []
        
        for ticker in tickers:
            # Validar preços
            price_validation = self.validate_prices(ticker)
            price_results.append(price_validation)
            
            # Validar fundamentos
            fundamental_validation = self.validate_fundamentals(ticker)
            fundamental_results.append(fundamental_validation)
        
        # Compilar estatísticas
        valid_prices = sum(1 for r in price_results if r['valid'])
        valid_fundamentals = sum(1 for r in fundamental_results if r['valid'])
        
        # Tickers válidos para backtest (ambos válidos)
        valid_for_backtest = []
        insufficient_for_backtest = []
        
        for i, ticker in enumerate(tickers):
            if price_results[i]['valid'] and fundamental_results[i]['valid']:
                valid_for_backtest.append(ticker)
            else:
                insufficient_for_backtest.append({
                    "ticker": ticker,
                    "price_valid": price_results[i]['valid'],
                    "fundamental_valid": fundamental_results[i]['valid'],
                    "price_issues": price_results[i]['issues'],
                    "fundamental_issues": fundamental_results[i]['issues']
                })
        
        # Estatísticas de anos
        years_list = []
        for result in price_results:
            if result['valid'] and 'years_span' in result['stats']:
                years_list.append(result['stats']['years_span'])
        
        summary = {
            "total_tickers_processed": len(tickers),
            "valid_prices": valid_prices,
            "valid_fundamentals": valid_fundamentals,
            "valid_for_backtest": len(valid_for_backtest),
            "insufficient_for_backtest": len(insufficient_for_backtest),
            "price_validation_rate": round(valid_prices / len(tickers) * 100, 2),
            "fundamental_validation_rate": round(valid_fundamentals / len(tickers) * 100, 2),
            "backtest_ready_rate": round(len(valid_for_backtest) / len(tickers) * 100, 2),
            "years_stats": {
                "min": round(min(years_list), 2) if years_list else 0,
                "max": round(max(years_list), 2) if years_list else 0,
                "avg": round(np.mean(years_list), 2) if years_list else 0,
                "median": round(np.median(years_list), 2) if years_list else 0
            }
        }
        
        logger.info("=" * 80)
        logger.info("RELATÓRIO DE VALIDAÇÃO")
        logger.info("=" * 80)
        logger.info(f"Total de tickers processados: {summary['total_tickers_processed']}")
        logger.info(f"Preços válidos: {summary['valid_prices']} ({summary['price_validation_rate']}%)")
        logger.info(f"Fundamentos válidos: {summary['valid_fundamentals']} ({summary['fundamental_validation_rate']}%)")
        logger.info(f"Prontos para backtest: {summary['valid_for_backtest']} ({summary['backtest_ready_rate']}%)")
        logger.info(f"Insuficientes para backtest: {summary['insufficient_for_backtest']}")
        logger.info("")
        logger.info("Estatísticas de anos disponíveis:")
        logger.info(f"  Mínimo: {summary['years_stats']['min']} anos")
        logger.info(f"  Máximo: {summary['years_stats']['max']} anos")
        logger.info(f"  Média: {summary['years_stats']['avg']} anos")
        logger.info(f"  Mediana: {summary['years_stats']['median']} anos")
        logger.info("=" * 80)
        
        return {
            "summary": summary,
            "valid_for_backtest": valid_for_backtest,
            "insufficient_for_backtest": insufficient_for_backtest,
            "price_results": price_results,
            "fundamental_results": fundamental_results
        }
