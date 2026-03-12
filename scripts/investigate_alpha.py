"""
Script para investigar o cálculo de alpha anômalo.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.models.database import SessionLocal
from app.models.schemas import RankingHistory
from datetime import date
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def investigate_alpha():
    """Investiga o cálculo de alpha"""
    
    db = SessionLocal()
    
    try:
        # Verificar período de dados
        first = db.query(RankingHistory).order_by(RankingHistory.date).first()
        last = db.query(RankingHistory).order_by(RankingHistory.date.desc()).first()
        
        if not first or not last:
            print("❌ Nenhum ranking snapshot encontrado")
            return
        
        print(f"\n📅 Período de Dados:")
        print(f"  Primeira data: {first.date}")
        print(f"  Última data: {last.date}")
        
        # Contar snapshots
        total_snapshots = db.query(RankingHistory.date).distinct().count()
        print(f"  Total de snapshots: {total_snapshots}")
        
        # Calcular duração
        duration_days = (last.date - first.date).days
        duration_years = duration_days / 365.25
        
        print(f"  Duração: {duration_days} dias ({duration_years:.2f} anos)")
        
        # Diagnóstico
        print(f"\n🔍 Diagnóstico:")
        
        if total_snapshots < 12:
            print(f"  ⚠️  PROBLEMA: Apenas {total_snapshots} snapshots (menos de 1 ano)")
            print(f"  ⚠️  Alpha anualizado com poucos dados fica distorcido")
            print(f"  ⚠️  Recomendação: Gerar mais snapshots históricos")
        
        if duration_years < 1.0:
            print(f"  ⚠️  PROBLEMA: Período muito curto ({duration_years:.2f} anos)")
            print(f"  ⚠️  Alpha anualizado não é confiável")
            print(f"  ⚠️  Recomendação: Usar período mínimo de 2-3 anos")
        
        # Calcular alpha esperado baseado em Sharpe
        sharpe = 0.96
        vol = 0.1918
        rf = 0.0
        
        expected_return = sharpe * vol + rf
        expected_alpha = expected_return * 100  # Em %
        
        print(f"\n📊 Alpha Esperado (baseado em Sharpe):")
        print(f"  Sharpe Ratio: {sharpe}")
        print(f"  Volatilidade: {vol*100:.2f}%")
        print(f"  Retorno esperado: {expected_return*100:.2f}%")
        print(f"  Alpha esperado: ~{expected_alpha:.2f}% (não 1192%!)")
        
        print(f"\n💡 Solução:")
        print(f"  1. Gerar snapshots históricos para 2-3 anos:")
        print(f"     docker exec -it quant-ranker-backend python scripts/generate_historical_scores.py \\")
        print(f"       --start 2022-01-01 --end 2026-03-01 --frequency monthly")
        print(f"  2. Executar backtest novamente")
        print(f"  3. Alpha deve ficar entre -50% e +50%")
        
    finally:
        db.close()

if __name__ == "__main__":
    investigate_alpha()
