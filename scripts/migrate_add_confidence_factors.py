#!/usr/bin/env python3
"""
Migração para adicionar campos de confidence factors ao schema.
Versão: 2.6.0 - Adaptive History
"""
import sys
from pathlib import Path

# Adicionar diretório raiz ao path
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

from sqlalchemy import text
from app.models.database import engine, SessionLocal

def migrate():
    """Adiciona colunas de confidence factors à tabela features_monthly."""
    
    print("=" * 80)
    print("MIGRAÇÃO: Adicionar Confidence Factors (v2.6.0)")
    print("=" * 80)
    print()
    
    with engine.connect() as conn:
        # Verificar se as colunas já existem
        result = conn.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'features_monthly' 
            AND column_name IN (
                'roe_mean_3y_confidence',
                'roe_volatility_confidence',
                'revenue_growth_3y_confidence',
                'net_income_volatility_confidence',
                'overall_confidence'
            )
        """))
        
        existing_columns = [row[0] for row in result]
        
        if len(existing_columns) == 5:
            print("✅ Todas as colunas de confidence já existem!")
            print()
            return
        
        print(f"📊 Colunas existentes: {len(existing_columns)}/5")
        print()
        
        # Adicionar colunas que não existem
        columns_to_add = [
            ('roe_mean_3y_confidence', 'FLOAT'),
            ('roe_volatility_confidence', 'FLOAT'),
            ('revenue_growth_3y_confidence', 'FLOAT'),
            ('net_income_volatility_confidence', 'FLOAT'),
            ('overall_confidence', 'FLOAT')
        ]
        
        for col_name, col_type in columns_to_add:
            if col_name not in existing_columns:
                print(f"➕ Adicionando coluna: {col_name}")
                try:
                    conn.execute(text(f"""
                        ALTER TABLE features_monthly 
                        ADD COLUMN {col_name} {col_type}
                    """))
                    conn.commit()
                    print(f"   ✅ {col_name} adicionada")
                except Exception as e:
                    print(f"   ⚠️  Erro ao adicionar {col_name}: {e}")
            else:
                print(f"   ⏭️  {col_name} já existe")
        
        print()
        print("=" * 80)
        print("✅ MIGRAÇÃO CONCLUÍDA")
        print("=" * 80)
        print()
        print("Próximos passos:")
        print("1. Executar pipeline para calcular confidence factors")
        print("2. Verificar que overall_confidence está sendo calculado")
        print("3. Aplicar confidence no scoring_engine")

if __name__ == "__main__":
    try:
        migrate()
    except Exception as e:
        print(f"❌ Erro na migração: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
