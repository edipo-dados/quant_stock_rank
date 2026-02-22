"""
Script para inserir dados de teste no banco de dados.
Usado quando as APIs externas não estão disponíveis.
"""

import sys
import os
from datetime import date, datetime, timedelta
from decimal import Decimal

# Adicionar diretório raiz ao path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.models.database import SessionLocal
from app.models.schemas import ScoreDaily

def insert_test_scores():
    """Insere scores de teste para demonstração."""
    db = SessionLocal()
    
    try:
        # Limpar scores existentes
        db.query(ScoreDaily).delete()
        db.commit()
        
        # Data de hoje
        today = date.today()
        
        # Dados de teste para 5 ativos
        test_data = [
            {
                "ticker": "PETR4.SA",
                "final_score": 0.85,
                "momentum_score": 0.90,
                "quality_score": 0.80,
                "value_score": 0.85,
                "confidence": 0.95,
                "rank": 1
            },
            {
                "ticker": "VALE3.SA",
                "final_score": 0.78,
                "momentum_score": 0.75,
                "quality_score": 0.82,
                "value_score": 0.77,
                "confidence": 0.92,
                "rank": 2
            },
            {
                "ticker": "ITUB4.SA",
                "final_score": 0.72,
                "momentum_score": 0.70,
                "quality_score": 0.75,
                "value_score": 0.71,
                "confidence": 0.88,
                "rank": 3
            },
            {
                "ticker": "BBDC4.SA",
                "final_score": 0.65,
                "momentum_score": 0.60,
                "quality_score": 0.70,
                "value_score": 0.66,
                "confidence": 0.85,
                "rank": 4
            },
            {
                "ticker": "WEGE3.SA",
                "final_score": 0.58,
                "momentum_score": 0.55,
                "quality_score": 0.62,
                "value_score": 0.57,
                "confidence": 0.80,
                "rank": 5
            }
        ]
        
        # Inserir dados
        for data in test_data:
            score = ScoreDaily(
                ticker=data["ticker"],
                date=today,
                final_score=data["final_score"],
                momentum_score=data["momentum_score"],
                quality_score=data["quality_score"],
                value_score=data["value_score"],
                confidence=data["confidence"],
                rank=data["rank"],
                calculated_at=datetime.utcnow()
            )
            db.add(score)
        
        db.commit()
        print(f"✓ Inseridos {len(test_data)} scores de teste para {today}")
        print("✓ Dados de teste prontos para visualização!")
        
    except Exception as e:
        db.rollback()
        print(f"✗ Erro ao inserir dados de teste: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    insert_test_scores()
