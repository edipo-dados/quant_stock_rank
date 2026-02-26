#!/bin/bash
# Script para corrigir dados antigos no EC2

echo "=========================================="
echo "FIX: Dados Antigos no EC2"
echo "=========================================="
echo ""

# 1. Verificar datas atuais
echo "1️⃣  Verificando datas dos dados..."
docker exec quant-ranker-backend python scripts/check_data_dates.py
echo ""

# 2. Perguntar se deseja limpar
read -p "Deseja limpar dados antigos e forçar atualização? (s/n): " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Ss]$ ]]; then
    echo ""
    echo "2️⃣  Limpando dados antigos..."
    docker exec quant-ranker-backend python -c "
from app.models.database import SessionLocal
from app.models.schemas import ScoreDaily
from datetime import date, timedelta

db = SessionLocal()
cutoff = date.today() - timedelta(days=7)
deleted = db.query(ScoreDaily).filter(ScoreDaily.date < cutoff).delete()
db.commit()
print(f'Scores antigos removidos: {deleted}')
db.close()
"
    echo ""
    
    echo "3️⃣  Executando pipeline FULL..."
    docker exec quant-ranker-backend python scripts/run_pipeline_docker.py --mode liquid --limit 50 --force-full
    echo ""
    
    echo "4️⃣  Verificando dados atualizados..."
    docker exec quant-ranker-backend python scripts/check_data_dates.py
    echo ""
    
    echo "5️⃣  Reiniciando containers..."
    docker-compose restart backend frontend
    echo ""
    
    echo "✅ Processo concluído!"
    echo ""
    echo "Acesse o frontend para verificar os dados atualizados."
else
    echo "❌ Operação cancelada"
fi
