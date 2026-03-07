"""Script para re-normalizar scores para range 0-1"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.models.database import SessionLocal
from app.models.schemas import RankingHistory
from datetime import date

db = SessionLocal()

print("\n" + "="*80)
print("RE-NORMALIZAÇÃO DE SCORES PARA 0-1")
print("="*80 + "\n")

# Buscar todos os rankings válidos (não futuros)
today = date.today()
rankings = db.query(RankingHistory).filter(
    RankingHistory.date <= today
).all()

print(f"Total de rankings: {len(rankings)}")

if not rankings:
    print("❌ Nenhum ranking encontrado!")
    db.close()
    exit(1)

# Coletar todos os scores
scores = [r.final_score for r in rankings if r.final_score is not None]

if not scores:
    print("❌ Nenhum score encontrado!")
    db.close()
    exit(1)

print(f"\nScores originais:")
print(f"  Mínimo: {min(scores):.4f}")
print(f"  Máximo: {max(scores):.4f}")
print(f"  Média: {sum(scores)/len(scores):.4f}")

# Re-normalizar para 0-1 usando min-max scaling
min_score = min(scores)
max_score = max(scores)
score_range = max_score - min_score

if score_range == 0:
    print("❌ Todos os scores são iguais!")
    db.close()
    exit(1)

print(f"\nRe-normalizando para 0-1...")

count = 0
for ranking in rankings:
    if ranking.final_score is not None:
        # Min-max normalization: (x - min) / (max - min)
        normalized = (ranking.final_score - min_score) / score_range
        ranking.final_score = normalized
        
        # Se houver smoothed score, normalizar também
        if ranking.final_score_smoothed is not None:
            normalized_smoothed = (ranking.final_score_smoothed - min_score) / score_range
            ranking.final_score_smoothed = normalized_smoothed
        
        count += 1
        
        if count % 1000 == 0:
            print(f"  Processados: {count}")

db.commit()

print(f"\n✓ {count} scores re-normalizados!")

# Verificar resultado
rankings_check = db.query(RankingHistory).filter(
    RankingHistory.date <= today
).all()

scores_check = [r.final_score for r in rankings_check if r.final_score is not None]

print(f"\nScores após normalização:")
print(f"  Mínimo: {min(scores_check):.4f}")
print(f"  Máximo: {max(scores_check):.4f}")
print(f"  Média: {sum(scores_check)/len(scores_check):.4f}")

print("\n" + "="*80 + "\n")

db.close()
