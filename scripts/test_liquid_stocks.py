"""Script para testar busca de ações mais líquidas da B3"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.ingestion.b3_liquid_stocks import B3LiquidStocksFetcher
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def main():
    """Testa busca de ações líquidas"""
    
    print("\n" + "="*80)
    print("TESTE: BUSCA DE AÇÕES MAIS LÍQUIDAS DA B3")
    print("="*80 + "\n")
    
    fetcher = B3LiquidStocksFetcher()
    
    # Teste 1: Top 50 com universo dinâmico
    print("\n--- TESTE 1: Top 50 ações mais líquidas (universo dinâmico) ---\n")
    tickers, details = fetcher.fetch_with_details(
        limit=50,
        lookback_days=30,
        min_volume=1_000_000.0,
        use_dynamic_universe=True
    )
    
    if not details.empty:
        print(f"\n✓ Encontradas {len(tickers)} ações líquidas\n")
        print("Top 20:")
        print("-" * 100)
        print(f"{'Rank':<6} {'Ticker':<12} {'Vol. Financeiro Médio':<25} {'Vol. Ações':<15} {'Preço Médio':<12}")
        print("-" * 100)
        
        for i, row in details.head(20).iterrows():
            print(
                f"{i+1:<6} {row['ticker']:<12} "
                f"R$ {row['avg_financial_volume']:>20,.2f}  "
                f"{row['avg_volume']:>12,.0f}  "
                f"R$ {row['avg_price']:>8.2f}"
            )
        print("-" * 100)
        
        # Verificar se ITUB3 está na lista
        itub3_ticker = 'ITUB3.SA'
        if itub3_ticker in tickers:
            rank = tickers.index(itub3_ticker) + 1
            itub3_data = details[details['ticker'] == itub3_ticker].iloc[0]
            print(f"\n✓ ITUB3 encontrado!")
            print(f"  Posição no ranking: {rank}")
            print(f"  Volume financeiro médio: R$ {itub3_data['avg_financial_volume']:,.2f}")
            print(f"  Volume de ações médio: {itub3_data['avg_volume']:,.0f}")
            print(f"  Preço médio: R$ {itub3_data['avg_price']:.2f}")
        else:
            print(f"\n❌ ITUB3 NÃO está entre as top {len(tickers)} mais líquidas")
    else:
        print("❌ Nenhuma ação encontrada!")
    
    # Teste 2: Comparar com lista fixa
    print("\n\n--- TESTE 2: Comparação com lista fixa (B3_UNIVERSE) ---\n")
    tickers_fixed, details_fixed = fetcher.fetch_with_details(
        limit=50,
        lookback_days=30,
        min_volume=1_000_000.0,
        use_dynamic_universe=False
    )
    
    print(f"Ações encontradas (universo dinâmico): {len(tickers)}")
    print(f"Ações encontradas (lista fixa): {len(tickers_fixed)}")
    
    # Ações que estão no dinâmico mas não na lista fixa
    new_stocks = set(tickers) - set(tickers_fixed)
    if new_stocks:
        print(f"\n✓ {len(new_stocks)} novas ações descobertas pelo universo dinâmico:")
        for ticker in list(new_stocks)[:10]:
            print(f"  - {ticker}")
    
    print("\n" + "="*80)
    print("FIM DO TESTE")
    print("="*80 + "\n")

if __name__ == "__main__":
    main()
