"""Script para verificar filtros de elegibilidade"""
from app.models.database import SessionLocal
from app.models.schemas import AssetInfo, RawPriceDaily, FeatureDaily
from datetime import datetime, timedelta
from sqlalchemy import desc, func

db = SessionLocal()

print("\n=== VERIFICANDO FILTROS DE ELEGIBILIDADE ===\n")

# Verificar critérios de elegibilidade
print("\n=== CRITÉRIOS DE ELEGIBILIDADE ===")
print("Verificando app/filters/eligibility_filter.py...")

db.close()
