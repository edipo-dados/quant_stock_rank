#!/usr/bin/env python3
"""
Script para verificar as datas dos dados no banco.
"""
from app.models.database import SessionLocal
from app.models.schemas import RawPriceDaily, RawFundamental, ScoreDaily
from sqlalchemy import func
from datetime import date, timedelta

def check_data_dates():
    """Verifica as datas dos dados no banco."""
    db = SessionLocal()
    
    try:
        print("=" * 80)
        print("VERIFICAÇÃO DE DATAS DOS DADOS")
        print("=" * 80)
        print()
        
        # Data de hoje
        today = date.today()
        print(f"📅 Data de hoje: {today}")
        print()
        
        # Verificar preços
        print("📊 PREÇOS DIÁRIOS (raw_prices_daily)")
        print("-" * 80)
        
        latest_price = db.query(func.max(RawPriceDaily.date)).scalar()
        oldest_price = db.query(func.min(RawPriceDaily.date)).scalar()
        total_prices = db.query(RawPriceDaily).count()
        tickers_with_prices = db.query(RawPriceDaily.ticker).distinct().count()
        
        print(f"Data mais antiga: {oldest_price}")
        print(f"Data mais recente: {latest_price}")
        print(f"Total de registros: {total_prices:,}")
        print(f"Tickers com preços: {tickers_with_prices}")
        
        if latest_price:
            days_old = (today - latest_price).days
            print(f"Idade dos dados: {days_old} dias")
            if days_old > 1:
                print(f"⚠️  ATENÇÃO: Dados de preços estão desatualizados!")
        print()
        
        # Verificar fundamentos
        print("💼 FUNDAMENTOS (raw_fundamentals)")
        print("-" * 80)
        
        latest_fundamental = db.query(func.max(RawFundamental.date)).scalar()
        oldest_fundamental = db.query(func.min(RawFundamental.date)).scalar()
        total_fundamentals = db.query(RawFundamental).count()
        tickers_with_fundamentals = db.query(RawFundamental.ticker).distinct().count()
        
        print(f"Data mais antiga: {oldest_fundamental}")
        print(f"Data mais recente: {latest_fundamental}")
        print(f"Total de registros: {total_fundamentals:,}")
        print(f"Tickers com fundamentos: {tickers_with_fundamentals}")
        
        if latest_fundamental:
            days_old = (today - latest_fundamental).days
            print(f"Idade dos dados: {days_old} dias")
            if days_old > 1:
                print(f"⚠️  ATENÇÃO: Dados de fundamentos estão desatualizados!")
        print()
        
        # Verificar scores
        print("🎯 SCORES (scores_daily)")
        print("-" * 80)
        
        latest_score = db.query(func.max(ScoreDaily.date)).scalar()
        oldest_score = db.query(func.min(ScoreDaily.date)).scalar()
        total_scores = db.query(ScoreDaily).count()
        tickers_with_scores = db.query(ScoreDaily.ticker).distinct().count()
        
        print(f"Data mais antiga: {oldest_score}")
        print(f"Data mais recente: {latest_score}")
        print(f"Total de registros: {total_scores:,}")
        print(f"Tickers com scores: {tickers_with_scores}")
        
        if latest_score:
            days_old = (today - latest_score).days
            print(f"Idade dos dados: {days_old} dias")
            if days_old > 1:
                print(f"⚠️  ATENÇÃO: Scores estão desatualizados!")
        print()
        
        # Verificar scores de hoje
        print("📈 SCORES DE HOJE")
        print("-" * 80)
        
        today_scores = db.query(ScoreDaily).filter(ScoreDaily.date == today).all()
        print(f"Scores de hoje ({today}): {len(today_scores)}")
        
        if today_scores:
            print("\nTop 5 scores de hoje:")
            for i, score in enumerate(today_scores[:5], 1):
                print(f"  {i}. {score.ticker}: {score.final_score:.3f}")
        else:
            print("❌ Nenhum score encontrado para hoje!")
            
            # Verificar última data com scores
            if latest_score:
                print(f"\nÚltima data com scores: {latest_score}")
                last_scores = db.query(ScoreDaily).filter(ScoreDaily.date == latest_score).all()
                print(f"Scores nessa data: {len(last_scores)}")
                print("\nTop 5 scores da última data:")
                for i, score in enumerate(last_scores[:5], 1):
                    print(f"  {i}. {score.ticker}: {score.final_score:.3f}")
        print()
        
        # Resumo
        print("=" * 80)
        print("RESUMO")
        print("=" * 80)
        
        all_ok = True
        
        if not latest_price or (today - latest_price).days > 1:
            print("❌ Preços desatualizados")
            all_ok = False
        else:
            print("✅ Preços atualizados")
            
        if not latest_fundamental or (today - latest_fundamental).days > 1:
            print("❌ Fundamentos desatualizados")
            all_ok = False
        else:
            print("✅ Fundamentos atualizados")
            
        if not latest_score or (today - latest_score).days > 1:
            print("❌ Scores desatualizados")
            all_ok = False
        else:
            print("✅ Scores atualizados")
        
        print()
        if all_ok:
            print("✅ Todos os dados estão atualizados!")
        else:
            print("⚠️  Alguns dados estão desatualizados. Execute o pipeline:")
            print("   docker exec quant-ranker-backend python scripts/run_pipeline_docker.py --mode liquid --limit 50")
        
    finally:
        db.close()

if __name__ == "__main__":
    check_data_dates()
