#!/usr/bin/env python3
"""
Script para forçar atualização dos dados, removendo dados antigos.
"""
import sys
from pathlib import Path

# Adicionar diretório raiz ao path
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

from datetime import date, timedelta
from app.models.database import SessionLocal
from app.models.schemas import RawPriceDaily, RawFundamental, ScoreDaily, FeatureDaily, FeatureMonthly
from sqlalchemy import func

def force_refresh_data(days_to_keep: int = 7):
    """
    Remove dados antigos para forçar atualização.
    
    Args:
        days_to_keep: Número de dias de dados a manter (padrão: 7)
    """
    db = SessionLocal()
    
    try:
        cutoff_date = date.today() - timedelta(days=days_to_keep)
        
        print("=" * 80)
        print("FORÇAR ATUALIZAÇÃO DE DADOS")
        print("=" * 80)
        print(f"Data de corte: {cutoff_date}")
        print(f"Mantendo dados dos últimos {days_to_keep} dias")
        print()
        
        # Contar registros antes
        print("📊 CONTAGEM ANTES DA LIMPEZA")
        print("-" * 80)
        
        prices_before = db.query(RawPriceDaily).count()
        fundamentals_before = db.query(RawFundamental).count()
        scores_before = db.query(ScoreDaily).count()
        features_daily_before = db.query(FeatureDaily).count()
        features_monthly_before = db.query(FeatureMonthly).count()
        
        print(f"Preços: {prices_before:,}")
        print(f"Fundamentos: {fundamentals_before:,}")
        print(f"Scores: {scores_before:,}")
        print(f"Features diárias: {features_daily_before:,}")
        print(f"Features mensais: {features_monthly_before:,}")
        print()
        
        # Confirmar
        response = input("⚠️  Deseja continuar com a limpeza? (sim/não): ")
        if response.lower() not in ['sim', 's', 'yes', 'y']:
            print("❌ Operação cancelada")
            return
        
        print()
        print("🗑️  REMOVENDO DADOS ANTIGOS...")
        print("-" * 80)
        
        # Remover preços antigos
        deleted_prices = db.query(RawPriceDaily).filter(
            RawPriceDaily.date < cutoff_date
        ).delete()
        print(f"Preços removidos: {deleted_prices:,}")
        
        # Remover fundamentos antigos
        deleted_fundamentals = db.query(RawFundamental).filter(
            RawFundamental.date < cutoff_date
        ).delete()
        print(f"Fundamentos removidos: {deleted_fundamentals:,}")
        
        # Remover scores antigos
        deleted_scores = db.query(ScoreDaily).filter(
            ScoreDaily.date < cutoff_date
        ).delete()
        print(f"Scores removidos: {deleted_scores:,}")
        
        # Remover features antigas
        deleted_features_daily = db.query(FeatureDaily).filter(
            FeatureDaily.date < cutoff_date
        ).delete()
        print(f"Features diárias removidas: {deleted_features_daily:,}")
        
        deleted_features_monthly = db.query(FeatureMonthly).filter(
            FeatureMonthly.date < cutoff_date
        ).delete()
        print(f"Features mensais removidas: {deleted_features_monthly:,}")
        
        db.commit()
        print()
        
        # Contar registros depois
        print("📊 CONTAGEM APÓS LIMPEZA")
        print("-" * 80)
        
        prices_after = db.query(RawPriceDaily).count()
        fundamentals_after = db.query(RawFundamental).count()
        scores_after = db.query(ScoreDaily).count()
        features_daily_after = db.query(FeatureDaily).count()
        features_monthly_after = db.query(FeatureMonthly).count()
        
        print(f"Preços: {prices_after:,}")
        print(f"Fundamentos: {fundamentals_after:,}")
        print(f"Scores: {scores_after:,}")
        print(f"Features diárias: {features_daily_after:,}")
        print(f"Features mensais: {features_monthly_after:,}")
        print()
        
        print("=" * 80)
        print("✅ LIMPEZA CONCLUÍDA")
        print("=" * 80)
        print()
        print("Próximos passos:")
        print("1. Execute o pipeline em modo FULL:")
        print("   docker exec quant-ranker-backend python scripts/run_pipeline_docker.py --mode liquid --limit 50 --force-full")
        print()
        print("2. Verifique os dados:")
        print("   docker exec quant-ranker-backend python scripts/check_data_dates.py")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Erro: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    days = 7
    if len(sys.argv) > 1:
        days = int(sys.argv[1])
    
    force_refresh_data(days)
