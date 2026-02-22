"""
Módulo para buscar os ativos mais líquidos da B3 (Bolsa de Valores do Brasil).

Este módulo usa o Yahoo Finance para identificar os ativos mais líquidos
baseado no volume médio de negociação.
"""

import logging
from datetime import date, timedelta
from typing import List, Dict, Tuple
import pandas as pd
import yfinance as yf

from app.ingestion.yfinance_config import configure_yfinance

logger = logging.getLogger(__name__)


# Lista de ativos da B3 para análise de liquidez
# Inclui as principais ações do Ibovespa e outros ativos líquidos
B3_UNIVERSE = [
    # Bancos
    "ITUB4.SA", "BBDC4.SA", "BBAS3.SA", "SANB11.SA", "BBDC3.SA", "ITUB3.SA",
    
    # Petróleo e Energia
    "PETR4.SA", "PETR3.SA", "PRIO3.SA", "CSAN3.SA", "UGPA3.SA", "EQTL3.SA",
    
    # Mineração e Siderurgia
    "VALE3.SA", "CSNA3.SA", "GGBR4.SA", "USIM5.SA",
    
    # Varejo
    "MGLU3.SA", "LREN3.SA", "ARZZ3.SA", "PCAR3.SA", "VIIA3.SA", "BHIA3.SA",
    "AMER3.SA", "ASAI3.SA", "CRFB3.SA",
    
    # Alimentos e Bebidas
    "ABEV3.SA", "JBSS3.SA", "BRFS3.SA", "SMTO3.SA", "BEEF3.SA",
    
    # Telecomunicações
    "VIVT3.SA", "TIMS3.SA",
    
    # Utilities (Energia Elétrica)
    "ELET3.SA", "ELET6.SA", "CMIG4.SA", "CPFE3.SA", "EGIE3.SA", "ENGI11.SA",
    "TAEE11.SA", "CPLE6.SA",
    
    # Construção e Imobiliário
    "MRVE3.SA", "CYRE3.SA", "EZTC3.SA", "MULT3.SA",
    
    # Papel e Celulose
    "SUZB3.SA", "KLBN11.SA",
    
    # Transporte e Logística
    "RAIL3.SA", "CCRO3.SA", "EMBR3.SA", "AZUL4.SA", "GOLL4.SA",
    
    # Saúde
    "RDOR3.SA", "HAPV3.SA", "FLRY3.SA", "GNDI3.SA", "QUAL3.SA",
    
    # Tecnologia
    "TOTS3.SA", "LWSA3.SA",
    
    # Educação
    "COGN3.SA", "YDUQ3.SA",
    
    # Seguros
    "BBSE3.SA", "CIEL3.SA",
    
    # Outros
    "WEGE3.SA", "RENT3.SA", "RADL3.SA", "B3SA3.SA", "NTCO3.SA",
    "BPAC11.SA", "SLCE3.SA", "RECV3.SA", "IGTI11.SA", "PETZ3.SA",
    "SOMA3.SA", "SBSP3.SA", "BRKM5.SA", "GOAU4.SA", "IRBR3.SA",
    "BRML3.SA", "POSI3.SA", "STBP3.SA", "DXCO3.SA", "ALOS3.SA"
]


class B3LiquidStocksFetcher:
    """Busca os ativos mais líquidos da B3."""
    
    def __init__(self):
        """Inicializa o fetcher."""
        configure_yfinance()
    
    def fetch_most_liquid_stocks(
        self,
        limit: int = 100,
        lookback_days: int = 30,
        min_volume: float = 1_000_000.0
    ) -> List[str]:
        """
        Busca os ativos mais líquidos da B3 baseado no volume médio.
        
        Args:
            limit: Número máximo de ativos a retornar
            lookback_days: Dias para calcular volume médio
            min_volume: Volume mínimo diário (em R$) para considerar
        
        Returns:
            Lista de tickers ordenados por liquidez (mais líquido primeiro)
        """
        logger.info(f"Fetching most liquid stocks from B3 universe ({len(B3_UNIVERSE)} stocks)")
        logger.info(f"Parameters: limit={limit}, lookback_days={lookback_days}, min_volume={min_volume:,.0f}")
        
        end_date = date.today()
        start_date = end_date - timedelta(days=lookback_days)
        
        liquidity_data = []
        
        for ticker in B3_UNIVERSE:
            try:
                # Buscar dados de volume
                ticker_obj = yf.Ticker(ticker)
                df = ticker_obj.history(start=start_date, end=end_date)
                
                if df.empty:
                    logger.debug(f"No data for {ticker}, skipping")
                    continue
                
                # Calcular volume médio (em quantidade de ações)
                avg_volume = df['Volume'].mean()
                
                # Calcular volume financeiro médio (volume * preço)
                df['financial_volume'] = df['Volume'] * df['Close']
                avg_financial_volume = df['financial_volume'].mean()
                
                # Preço médio
                avg_price = df['Close'].mean()
                
                # Verificar se atende ao volume mínimo
                if avg_financial_volume < min_volume:
                    logger.debug(
                        f"{ticker}: avg_financial_volume={avg_financial_volume:,.0f} < "
                        f"min_volume={min_volume:,.0f}, skipping"
                    )
                    continue
                
                liquidity_data.append({
                    'ticker': ticker,
                    'avg_volume': avg_volume,
                    'avg_financial_volume': avg_financial_volume,
                    'avg_price': avg_price,
                    'days_with_data': len(df)
                })
                
                logger.debug(
                    f"{ticker}: avg_volume={avg_volume:,.0f}, "
                    f"avg_financial_volume={avg_financial_volume:,.0f}, "
                    f"avg_price={avg_price:.2f}"
                )
                
            except Exception as e:
                logger.warning(f"Error fetching data for {ticker}: {e}")
                continue
        
        if not liquidity_data:
            logger.error("No liquid stocks found!")
            return []
        
        # Ordenar por volume financeiro médio (mais líquido primeiro)
        liquidity_df = pd.DataFrame(liquidity_data)
        liquidity_df = liquidity_df.sort_values('avg_financial_volume', ascending=False)
        
        # Limitar ao número solicitado
        top_liquid = liquidity_df.head(limit)
        
        logger.info(f"\nTop {len(top_liquid)} most liquid stocks:")
        logger.info("-" * 80)
        for i, row in top_liquid.iterrows():
            logger.info(
                f"{row['ticker']:10s} - "
                f"Avg Volume: {row['avg_volume']:>12,.0f} shares, "
                f"Avg Financial Volume: R$ {row['avg_financial_volume']:>15,.2f}, "
                f"Avg Price: R$ {row['avg_price']:>8.2f}"
            )
        logger.info("-" * 80)
        
        return top_liquid['ticker'].tolist()
    
    def fetch_with_details(
        self,
        limit: int = 100,
        lookback_days: int = 30,
        min_volume: float = 1_000_000.0
    ) -> Tuple[List[str], pd.DataFrame]:
        """
        Busca os ativos mais líquidos com detalhes completos.
        
        Args:
            limit: Número máximo de ativos a retornar
            lookback_days: Dias para calcular volume médio
            min_volume: Volume mínimo diário (em R$) para considerar
        
        Returns:
            Tupla (lista de tickers, DataFrame com detalhes de liquidez)
        """
        logger.info(f"Fetching most liquid stocks with details")
        
        end_date = date.today()
        start_date = end_date - timedelta(days=lookback_days)
        
        liquidity_data = []
        
        for ticker in B3_UNIVERSE:
            try:
                ticker_obj = yf.Ticker(ticker)
                df = ticker_obj.history(start=start_date, end=end_date)
                
                if df.empty:
                    continue
                
                avg_volume = df['Volume'].mean()
                df['financial_volume'] = df['Volume'] * df['Close']
                avg_financial_volume = df['financial_volume'].mean()
                avg_price = df['Close'].mean()
                
                if avg_financial_volume < min_volume:
                    continue
                
                liquidity_data.append({
                    'ticker': ticker,
                    'avg_volume': avg_volume,
                    'avg_financial_volume': avg_financial_volume,
                    'avg_price': avg_price,
                    'days_with_data': len(df),
                    'min_price': df['Close'].min(),
                    'max_price': df['Close'].max(),
                    'volatility': df['Close'].std() / df['Close'].mean() if df['Close'].mean() > 0 else 0
                })
                
            except Exception as e:
                logger.warning(f"Error fetching data for {ticker}: {e}")
                continue
        
        if not liquidity_data:
            return [], pd.DataFrame()
        
        liquidity_df = pd.DataFrame(liquidity_data)
        liquidity_df = liquidity_df.sort_values('avg_financial_volume', ascending=False)
        top_liquid = liquidity_df.head(limit)
        
        return top_liquid['ticker'].tolist(), top_liquid


def fetch_most_liquid_stocks(limit: int = 100) -> List[str]:
    """
    Função de conveniência para buscar os ativos mais líquidos.
    
    Args:
        limit: Número máximo de ativos a retornar (default: 100)
    
    Returns:
        Lista de tickers ordenados por liquidez
    """
    fetcher = B3LiquidStocksFetcher()
    return fetcher.fetch_most_liquid_stocks(limit=limit)
