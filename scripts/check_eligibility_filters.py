"""Script para verificar filtros de elegibilidade"""
from app.models.database import SessionLocal
from app.models.schemas import AssetInfo, RawPriceDaily, FeatureDaily
from datetime import datetime, timedelta
from sqlalchemy import desc, func

db = SessionLocal()

print("\n=== VERIFICANDO FILTROS DE ELEGIBILIDADE ===\n")

# Verificar ITUB3 especificamente
itub3 = db.query(AssetInfo).filter(AssetInfo.ticker == 'ITUB3').first()

if itub3:
    print(f"ITUB3 - Status atual:")
    print(f"  is_active: {itub3.is_active}")
    print(f"  is_eligible: {itub3.is_eligible}")
    
    # Verificar dados recentes
    recent_date = datetime.now() - timedelta(days=60)
    
    # Preços
    price_count = db.query(func.count(RawPriceDaily.id)).filter(
        RawPriceDaily.ticker == 'ITUB3',
        RawPriceDaily.date >= recent_date
    ).scalar()
    
    latest_price = db.query(RawPriceDaily).filter(
        RawPriceDaily.ticker == 'ITUB3'
    ).order_by(desc(RawPriceDaily.date)).first()
    
    print(f"\n  Preços nos últimos 60 dias: {price_count}")
    if latest_price:
        print(f"  Último preço: {latest_price.date} - Close: {latest_price.close}, Volume: {latest_price.volume}")
    
    # Features
    feature_count = db.query(func.count(FeatureDaily.id)).filter(
        FeatureDaily.ticker == 'ITUB3',
        FeatureDaily.date >= recent_date
    ).scalar()
    
    latest_feature = db.query(FeatureDaily).filter(
        FeatureDaily.ticker == 'ITUB3'
    ).order_by(desc(FeatureDaily.date)).first()
    
    print(f"  Features nos últimos 60 dias: {feature_count}")
    if latest_feature:
        print(f"  Última feature: {latest_feature.date}")
        print(f"    market_cap: {latest_feature.market_cap}")
        print(f"    avg_volume_20d: {latest_feature.avg_volume_20d}")
        print(f"    avg_dollar_volume_20d: {latest_feature.avg_dollar_volume_20d}")

else:
    print("ITUB3 não encontrado!")

# Verificar critérios de elegibilidade
print("\n=== CRITÉRIOS DE ELEGIBILIDADE ===")
print("Verificando app/filters/eligibility_filter.py...")

db.close()
