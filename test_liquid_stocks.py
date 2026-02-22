"""
Script de teste para validar a busca de ativos líquidos da B3.
"""

import logging
from app.ingestion.b3_liquid_stocks import B3LiquidStocksFetcher

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def test_fetch_top_10():
    """Testa busca dos top 10 mais líquidos."""
    logger.info("=" * 80)
    logger.info("TESTE: Top 10 Ativos Mais Líquidos")
    logger.info("=" * 80)
    
    fetcher = B3LiquidStocksFetcher()
    tickers = fetcher.fetch_most_liquid_stocks(limit=10, lookback_days=30)
    
    logger.info(f"\nResultado: {len(tickers)} ativos encontrados")
    logger.info(f"Tickers: {', '.join(tickers)}")
    
    assert len(tickers) > 0, "Deveria encontrar pelo menos 1 ativo"
    assert len(tickers) <= 10, "Não deveria retornar mais de 10 ativos"
    
    logger.info("✓ Teste passou!")
    return tickers


def test_fetch_top_50():
    """Testa busca dos top 50 mais líquidos."""
    logger.info("\n" + "=" * 80)
    logger.info("TESTE: Top 50 Ativos Mais Líquidos")
    logger.info("=" * 80)
    
    fetcher = B3LiquidStocksFetcher()
    tickers = fetcher.fetch_most_liquid_stocks(limit=50, lookback_days=30)
    
    logger.info(f"\nResultado: {len(tickers)} ativos encontrados")
    
    assert len(tickers) > 0, "Deveria encontrar pelo menos 1 ativo"
    assert len(tickers) <= 50, "Não deveria retornar mais de 50 ativos"
    
    logger.info("✓ Teste passou!")
    return tickers


def test_fetch_with_details():
    """Testa busca com detalhes completos."""
    logger.info("\n" + "=" * 80)
    logger.info("TESTE: Busca com Detalhes Completos")
    logger.info("=" * 80)
    
    fetcher = B3LiquidStocksFetcher()
    tickers, details_df = fetcher.fetch_with_details(limit=10, lookback_days=30)
    
    logger.info(f"\nResultado: {len(tickers)} ativos encontrados")
    logger.info(f"\nDetalhes do DataFrame:")
    logger.info(f"Colunas: {list(details_df.columns)}")
    logger.info(f"Shape: {details_df.shape}")
    
    if not details_df.empty:
        logger.info("\nPrimeiros 5 ativos:")
        logger.info(details_df.head().to_string())
    
    assert len(tickers) > 0, "Deveria encontrar pelo menos 1 ativo"
    assert not details_df.empty, "DataFrame não deveria estar vazio"
    assert 'ticker' in details_df.columns, "DataFrame deveria ter coluna 'ticker'"
    assert 'avg_financial_volume' in details_df.columns, "DataFrame deveria ter coluna 'avg_financial_volume'"
    
    logger.info("\n✓ Teste passou!")
    return tickers, details_df


def test_min_volume_filter():
    """Testa filtro de volume mínimo."""
    logger.info("\n" + "=" * 80)
    logger.info("TESTE: Filtro de Volume Mínimo")
    logger.info("=" * 80)
    
    fetcher = B3LiquidStocksFetcher()
    
    # Buscar com volume mínimo baixo
    tickers_low = fetcher.fetch_most_liquid_stocks(
        limit=100,
        lookback_days=30,
        min_volume=100_000  # R$ 100k
    )
    
    # Buscar com volume mínimo alto
    tickers_high = fetcher.fetch_most_liquid_stocks(
        limit=100,
        lookback_days=30,
        min_volume=10_000_000  # R$ 10M
    )
    
    logger.info(f"\nCom min_volume=100k: {len(tickers_low)} ativos")
    logger.info(f"Com min_volume=10M: {len(tickers_high)} ativos")
    
    assert len(tickers_low) >= len(tickers_high), \
        "Volume mínimo menor deveria retornar mais ou igual ativos"
    
    logger.info("✓ Teste passou!")
    return tickers_low, tickers_high


if __name__ == "__main__":
    try:
        # Executar testes
        logger.info("Iniciando testes de busca de ativos líquidos...\n")
        
        top_10 = test_fetch_top_10()
        top_50 = test_fetch_top_50()
        tickers_details, df_details = test_fetch_with_details()
        tickers_low, tickers_high = test_min_volume_filter()
        
        logger.info("\n" + "=" * 80)
        logger.info("TODOS OS TESTES PASSARAM! ✓")
        logger.info("=" * 80)
        
        logger.info(f"\nResumo:")
        logger.info(f"- Top 10 mais líquidos: {len(top_10)} ativos")
        logger.info(f"- Top 50 mais líquidos: {len(top_50)} ativos")
        logger.info(f"- Busca com detalhes: {len(tickers_details)} ativos")
        logger.info(f"- Filtro volume baixo: {len(tickers_low)} ativos")
        logger.info(f"- Filtro volume alto: {len(tickers_high)} ativos")
        
    except Exception as e:
        logger.error(f"Teste falhou: {e}", exc_info=True)
        exit(1)
