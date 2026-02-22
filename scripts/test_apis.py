"""
Script para testar conectividade com APIs externas.
"""

import logging
import sys
import os
from datetime import date, timedelta

# Adicionar diretório raiz ao path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.config import settings
from app.ingestion.yahoo_client import YahooFinanceClient
from app.ingestion.yahoo_finance_client import YahooFinanceClient as YahooFundamentalsClient

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def test_yahoo_finance_prices():
    """Testa conectividade com Yahoo Finance para preços."""
    try:
        logger.info("Testando Yahoo Finance (Preços)...")
        client = YahooFinanceClient()
        
        # Testar com um ticker brasileiro
        end_date = date.today()
        start_date = end_date - timedelta(days=7)
        
        df = client.fetch_daily_prices("PETR4.SA", start_date, end_date)
        
        if not df.empty:
            logger.info(f"✓ Yahoo Finance (Preços) OK - {len(df)} dias de dados para PETR4.SA")
            return True
        else:
            logger.warning("✗ Yahoo Finance (Preços) retornou dados vazios")
            return False
            
    except Exception as e:
        logger.error(f"✗ Yahoo Finance (Preços) FALHOU: {e}")
        return False


def test_yahoo_finance_fundamentals():
    """Testa conectividade com Yahoo Finance para dados fundamentalistas."""
    try:
        logger.info("Testando Yahoo Finance (Fundamentalistas)...")
        client = YahooFundamentalsClient()
        
        # Testar com um ticker brasileiro
        data = client.fetch_all_fundamentals("PETR4.SA", period="annual")
        
        if data and len(data.get("income_statement", [])) > 0:
            logger.info(f"✓ Yahoo Finance (Fundamentalistas) OK - Dados recebidos para PETR4.SA")
            return True
        else:
            logger.warning("✗ Yahoo Finance (Fundamentalistas) retornou dados vazios")
            return False
            
    except Exception as e:
        logger.error(f"✗ Yahoo Finance (Fundamentalistas) FALHOU: {e}")
        return False


def main():
    """Testa todas as APIs."""
    logger.info("=" * 80)
    logger.info("TESTE DE CONECTIVIDADE COM APIS EXTERNAS")
    logger.info("=" * 80)
    logger.info("")
    
    yahoo_prices_ok = test_yahoo_finance_prices()
    logger.info("")
    
    yahoo_fundamentals_ok = test_yahoo_finance_fundamentals()
    logger.info("")
    
    logger.info("=" * 80)
    logger.info("RESULTADO DOS TESTES")
    logger.info("=" * 80)
    logger.info(f"Yahoo Finance (Preços): {'✓ OK' if yahoo_prices_ok else '✗ FALHOU'}")
    logger.info(f"Yahoo Finance (Fundamentalistas): {'✓ OK' if yahoo_fundamentals_ok else '✗ FALHOU'}")
    logger.info("")
    
    if yahoo_prices_ok and yahoo_fundamentals_ok:
        logger.info("✓ Todas as APIs estão funcionando!")
        return 0
    elif yahoo_prices_ok or yahoo_fundamentals_ok:
        logger.warning("⚠ Algumas APIs estão funcionando, outras não")
        return 1
    else:
        logger.error("✗ Nenhuma API está funcionando")
        return 2


if __name__ == "__main__":
    sys.exit(main())
