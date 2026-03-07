"""Script para remover sufixo .SA dos tickers no RankingHistory"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.models.database import SessionLocal
from app.models.schemas import RankingHistory

db = SessionLocal()

print("\n" + "="*80)
print("CORRIGINDO TICKERS NO RANKING HISTORY")
print("="*80 + "\n")

# Buscar todos os rankings com .SA
rankings_with_sa = db.query(RankingHistory).filter(
    RankingHistory.ticker.like('%.SA')
).all()

print(f"Encontrados {len(rankings_with_sa)} registros com sufixo .SA")

if len(rankings_with_sa) == 0:
    print("✓ Nenhuma correção necessária!")
    db.close()
    exit(0)

print("\nCorrigindo...")

count = 0
for ranking in rankings_with_sa:
    # Remover .SA
    ranking.ticker = ranking.ticker.replace('.SA', '')
    count += 1
    
    if count % 1000 == 0:
        print(f"  Processados: {count}")

db.commit()

print(f"\n✓ {count} registros corrigidos!")

# Verificar
remaining = db.query(RankingHistory).filter(
    RankingHistory.ticker.like('%.SA')
).count()

print(f"Registros restantes com .SA: {remaining}")

print("\n" + "="*80 + "\n")

db.close()
