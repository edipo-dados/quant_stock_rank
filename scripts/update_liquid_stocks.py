"""Script para atualizar lista de ações líquidas no banco de dados"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.ingestion.b3_liquid_stocks import B3LiquidStocksFetcher
from app.models.database import SessionLocal
from app.models.schemas import AssetInfo
import logging
from datetime import datetime

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def update_liquid_stocks(
    limit: int = 100,
    lookback_days: int = 30,
    min_volume: float = 1_000_000.0,
    use_dynamic_universe: bool = True
):
    """
    Atualiza lista de ações líquidas no banco de dados.
    
    Args:
        limit: Número máximo de ações
        lookback_days: Dias para calcular liquidez
        min_volume: Volume mínimo em R$
        use_dynamic_universe: Usar universo dinâmico
    """
    print("\n" + "="*80)
    print("ATUALIZAÇÃO DE AÇÕES LÍQUIDAS")
    print("="*80 + "\n")
    
    # Buscar ações líquidas
    fetcher = B3LiquidStocksFetcher()
    tickers, details = fetcher.fetch_with_details(
        limit=limit,
        lookback_days=lookback_days,
        min_volume=min_volume,
        use_dynamic_universe=use_dynamic_universe
    )
    
    if not tickers:
        print("❌ Nenhuma ação líquida encontrada!")
        return
    
    print(f"\n✓ Encontradas {len(tickers)} ações líquidas")
    
    # Conectar ao banco
    db = SessionLocal()
    
    try:
        # Remover sufixo .SA dos tickers
        tickers_clean = [t.replace('.SA', '') for t in tickers]
        
        # Verificar quais já existem
        existing = db.query(AssetInfo).filter(
            AssetInfo.ticker.in_(tickers_clean)
        ).all()
        
        existing_tickers = {a.ticker for a in existing}
        new_tickers = set(tickers_clean) - existing_tickers
        
        print(f"\nStatus no banco de dados:")
        print(f"  Já existem: {len(existing_tickers)}")
        print(f"  Novos: {len(new_tickers)}")
        
        # Adicionar novos ativos
        if new_tickers:
            print(f"\nAdicionando {len(new_tickers)} novos ativos:")
            for ticker in new_tickers:
                ticker_with_sa = f"{ticker}.SA"
                if ticker_with_sa in tickers:
                    idx = tickers.index(ticker_with_sa)
                    row = details.iloc[idx]
                    
                    asset = AssetInfo(
                        ticker=ticker,
                        name=ticker,  # Nome será atualizado depois
                        is_active=True,
                        is_eligible=True,  # Será validado pelo filtro de elegibilidade
                        created_at=datetime.now(),
                        updated_at=datetime.now()
                    )
                    db.add(asset)
                    print(f"  + {ticker}")
            
            db.commit()
            print(f"\n✓ {len(new_tickers)} novos ativos adicionados")
        
        # Atualizar status de ativos existentes
        print(f"\nAtualizando status de ativos existentes...")
        for asset in existing:
            if asset.ticker in tickers_clean:
                if not asset.is_active:
                    asset.is_active = True
                    asset.updated_at = datetime.now()
                    print(f"  ✓ {asset.ticker} reativado")
        
        db.commit()
        
        # Desativar ativos que não estão mais líquidos
        all_assets = db.query(AssetInfo).filter(AssetInfo.is_active == True).all()
        inactive_count = 0
        
        for asset in all_assets:
            if asset.ticker not in tickers_clean:
                asset.is_active = False
                asset.updated_at = datetime.now()
                inactive_count += 1
                print(f"  - {asset.ticker} desativado (não está mais líquido)")
        
        if inactive_count > 0:
            db.commit()
            print(f"\n✓ {inactive_count} ativos desativados")
        
        # Resumo final
        print("\n" + "="*80)
        print("RESUMO")
        print("="*80)
        print(f"Total de ativos líquidos: {len(tickers_clean)}")
        print(f"Novos ativos adicionados: {len(new_tickers)}")
        print(f"Ativos desativados: {inactive_count}")
        
        # Verificar ITUB3
        itub3 = db.query(AssetInfo).filter(AssetInfo.ticker == 'ITUB3').first()
        if itub3:
            print(f"\n✓ ITUB3 status:")
            print(f"  is_active: {itub3.is_active}")
            print(f"  is_eligible: {itub3.is_eligible}")
        else:
            print(f"\n❌ ITUB3 não encontrado no banco!")
        
        print("="*80 + "\n")
        
    except Exception as e:
        logger.error(f"Erro ao atualizar banco de dados: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Atualizar lista de ações líquidas')
    parser.add_argument('--limit', type=int, default=100, help='Número máximo de ações')
    parser.add_argument('--days', type=int, default=30, help='Dias para calcular liquidez')
    parser.add_argument('--min-volume', type=float, default=1_000_000.0, help='Volume mínimo em R$')
    parser.add_argument('--no-dynamic', action='store_true', help='Não usar universo dinâmico')
    
    args = parser.parse_args()
    
    update_liquid_stocks(
        limit=args.limit,
        lookback_days=args.days,
        min_volume=args.min_volume,
        use_dynamic_universe=not args.no_dynamic
    )
