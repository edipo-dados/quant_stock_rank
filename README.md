# Quant Stock Ranker v2.6.0

Sistema de ranking quantitativo de ações brasileiras baseado em fatores acadêmicos (Momentum, Quality, Value, Size) com histórico adaptativo.

## 🎯 Características

- **Histórico Adaptativo (v2.6.0)**: Usa 1-3 anos de dados sem exigir exatamente 3 anos
- **Confidence Factors**: Rastreia qualidade dos dados e aplica ao quality_score
- **Arquitetura de 3 Camadas**: Elegibilidade estrutural → Feature engineering → Scoring
- **Tratamento Estatístico de Missing Values**: Imputação com medianas setoriais/universais
- **Sem Valores Sentinela**: Sistema usa NaN e redistribuição de pesos
- **Scores Normalizados**: Distribuição entre -3 e +3, média ~0
- **Pipeline Determinístico**: Mesmos inputs = mesmos outputs
- **Taxa de Elegibilidade**: >= 80% dos ativos passam filtro estrutural

## 📊 Metodologia

### Fatores Acadêmicos

**Momentum (35%)**
- momentum_6m_ex_1m: Retorno 6 meses excluindo último mês
- momentum_12m_ex_1m: Retorno 12 meses excluindo último mês
- volatility_90d: Volatilidade 90 dias (invertido)
- recent_drawdown: Drawdown recente (invertido)

**Quality (25%)** - Com Confidence Factor
- roe_mean_3y: ROE médio (1-3 anos disponíveis)
- roe_volatility: Volatilidade do ROE (invertido)
- net_margin: Margem líquida
- revenue_growth_3y: Crescimento de receita (1-3 anos)
- debt_to_ebitda: Dívida/EBITDA (invertido)
- **overall_confidence**: Fator de confiança aplicado ao score (0.33-1.0)

**Value (30%)**
- pe_ratio: P/L (invertido)
- price_to_book: P/B (invertido) - com fallback para pb_ratio
- ev_ebitda: EV/EBITDA (invertido)
- fcf_yield: FCF Yield

**Size (10%)**
- size_factor: -log(market_cap)

### Histórico Adaptativo (v2.6.0)

O sistema agora usa o máximo de dados disponíveis:

- **3+ anos**: Usa 3 anos completos (confidence = 1.0)
- **2 anos**: Usa 2 anos (confidence = 0.66)
- **1 ano**: Usa 1 ano (confidence = 0.33)
- **0 anos**: Retorna None (será imputado)

**Confidence Factor**: Aplicado ao quality_score para reduzir peso de ativos com histórico limitado.

Exemplo:
- Ativo com 3 anos: quality_score = 0.5 * 1.0 = 0.5
- Ativo com 2 anos: quality_score = 0.5 * 0.66 = 0.33
- Ativo com 1 ano: quality_score = 0.5 * 0.33 = 0.165

### Filtro de Elegibilidade Estrutural

Exclui apenas ativos com problemas estruturais graves:
- Patrimônio líquido <= 0
- EBITDA <= 0 (exceto bancos)
- Receita <= 0
- Volume médio < 100k
- Lucro líquido negativo (último ano)
- Lucro negativo em 2 dos últimos 3 anos
- Dívida líquida/EBITDA > 8

**NUNCA exclui por ausência de fatores derivados** (momentum, quality, value).

### Tratamento de Missing Values

1. **Cálculo de Features**: Usa histórico adaptativo, mantém NaN quando dados insuficientes
2. **Imputação**: Antes da normalização
   - Mediana setorial (se setor >= 5 ativos)
   - Mediana universal (fallback)
3. **Normalização**: Z-score cross-sectional + winsorização ±3σ
   - **Confidence factors NÃO são normalizados** (são metadados)
4. **Scoring**: 
   - Aplica confidence factor ao quality_score
   - Redistribui pesos quando categorias têm NaN

## 🚀 Quick Start

### Docker Local

```bash
# Iniciar containers
docker-compose up -d

# Rodar pipeline de teste (10 ativos)
docker exec quant-ranker-backend python scripts/run_pipeline_docker.py --mode test --limit 10

# Rodar pipeline produção (50 ativos)
docker exec quant-ranker-backend python scripts/run_pipeline_docker.py --mode liquid --limit 50

# Verificar scores
docker exec quant-ranker-backend python scripts/check_latest_scores.py

# Acessar frontend
http://localhost:8501
```

### EC2 Deploy (v2.6.0)

```bash
# 1. Clone e configure
git clone https://github.com/edipo-dados/quant_stock_rank
cd quant_stock_rank
cp .env.example .env
# Editar .env com suas credenciais

# 2. Build e start
docker-compose up -d --build

# 3. Aguardar containers ficarem healthy
sleep 30
docker-compose ps

# 4. Executar migration (v2.6.0)
docker exec quant-ranker-backend python scripts/migrate_add_confidence_factors.py

# 5. Rodar pipeline
docker exec quant-ranker-backend python scripts/run_pipeline_docker.py --mode liquid --limit 50

# 6. Verificar scores
docker exec quant-ranker-backend python scripts/check_latest_scores.py

# 7. Configurar cron job (execução diária às 19h)
crontab -e
# Adicionar:
0 19 * * * cd ~/quant_stock_rank && docker exec quant-ranker-backend python scripts/run_pipeline_docker.py --mode liquid --limit 50 >> /var/log/pipeline.log 2>&1
```

## 📁 Estrutura do Projeto

```
quant_stock_rank/
├── app/
│   ├── api/              # FastAPI endpoints
│   ├── backtest/         # Backtesting engine
│   ├── chat/             # Gemini chat integration
│   ├── confidence/       # Confidence scoring
│   ├── core/             # Core exceptions
│   ├── factor_engine/    # Feature calculation
│   │   ├── momentum_factors.py
│   │   ├── fundamental_factors.py
│   │   ├── financial_factors.py
│   │   ├── normalizer.py
│   │   ├── missing_handler.py  # NEW: Missing value imputation
│   │   └── feature_service.py
│   ├── filters/          # Eligibility filter
│   ├── ingestion/        # Data ingestion (Yahoo Finance, FMP)
│   ├── models/           # Database models
│   ├── report/           # Report generation
│   └── scoring/          # Scoring engine
├── frontend/             # Streamlit UI
├── scripts/              # Pipeline scripts
├── docs/                 # Documentation
└── deploy/               # Deployment guides
```

## 📖 Documentação

- **[PIPELINE_ARCHITECTURE.md](docs/PIPELINE_ARCHITECTURE.md)**: Arquitetura de 3 camadas
- **[CALCULOS_RANKING.md](docs/CALCULOS_RANKING.md)**: Cálculos detalhados
- **[MISSING_VALUE_TREATMENT.md](docs/MISSING_VALUE_TREATMENT.md)**: Tratamento de missing values
- **[EC2_DEPLOY_V2.5.1.md](EC2_DEPLOY_V2.5.1.md)**: Guia de deploy no EC2
- **[GUIA_USO.md](docs/GUIA_USO.md)**: Guia de uso completo

## 🔧 Comandos Úteis

### Pipeline

```bash
# Teste (5 ativos, rápido)
docker exec quant-ranker-backend python scripts/run_pipeline_docker.py --mode test --limit 10

# Produção incremental (50 ativos, ~2 min)
docker exec quant-ranker-backend python scripts/run_pipeline_docker.py --mode liquid --limit 50

# Produção FULL (50 ativos, ~15 min, busca histórico completo)
docker exec quant-ranker-backend python scripts/run_pipeline_docker.py --mode liquid --limit 50 --force-full
```

### Verificação

```bash
# Ver logs
docker-compose logs -f backend

# Verificar scores
docker exec quant-ranker-backend python -c "
from app.models.database import SessionLocal
from app.models.schemas import ScoreDaily
from datetime import date
import numpy as np

db = SessionLocal()
scores = db.query(ScoreDaily).filter(ScoreDaily.date == date.today()).all()
final_scores = [s.final_score for s in scores]
print(f'Scores: {len(scores)}')
print(f'Média: {np.mean(final_scores):.2f}')
print(f'Desvio: {np.std(final_scores):.2f}')
print(f'Range: [{np.min(final_scores):.2f}, {np.max(final_scores):.2f}]')
db.close()
"

# Verificar containers
docker-compose ps
```

### Manutenção

```bash
# Restart
docker-compose restart

# Rebuild
docker-compose down
docker-compose up -d --build

# Limpar espaço
docker system prune -a -f

# Backup banco
docker exec quant-ranker-db pg_dump -U postgres quant_ranker > backup.sql

# Restore banco
cat backup.sql | docker exec -i quant-ranker-db psql -U postgres quant_ranker
```

## 📊 Resultados Esperados

### Distribuição de Scores

```
Média: ~0.00
Desvio padrão: 0.2 - 0.5
Range: [-3, +3]
```

### Taxa de Elegibilidade

```
>= 80% dos ativos devem passar filtro estrutural
```

### Performance

```
Teste (5 ativos): ~12s
Incremental (50 ativos): ~2 min
FULL (50 ativos): ~15 min
```

## 🔒 Variáveis de Ambiente

```bash
# .env
DATABASE_URL=postgresql://postgres:postgres@db:5432/quant_ranker
FMP_API_KEY=your_fmp_key_here
GEMINI_API_KEY=your_gemini_key_here
MINIMUM_VOLUME=100000
```

## 🐛 Troubleshooting

### Taxa de Elegibilidade < 80%

**Causa**: Dados fundamentais incompletos

**Solução**:
```bash
# Verificar fundamentos
docker exec quant-ranker-backend python -c "
from app.models.database import SessionLocal
from app.models.schemas import RawFundamental
db = SessionLocal()
count = db.query(RawFundamental).count()
print(f'Fundamentos: {count}')
db.close()
"

# Se baixo, rodar FULL
docker exec quant-ranker-backend python scripts/run_pipeline_docker.py --mode liquid --limit 50 --force-full
```

### Scores Muito Baixos

**Normal!** Scores baixos indicam que alguns fatores críticos ainda estão sendo calculados (roe_mean_3y, price_to_book). Com o tempo e mais histórico, os scores melhoram.

### Containers Não Sobem

```bash
# Verificar espaço
df -h

# Limpar
docker system prune -a -f

# Verificar logs
docker-compose logs
```

## 📝 Changelog

### v2.5.2 (2026-02-26)
- ✅ Remoção completa de valores sentinela (-999)
- ✅ Tratamento estatístico correto de missing values
- ✅ Redistribuição automática de pesos
- ✅ Scores distribuídos entre -3 e +3

### v2.5.1 (2026-02-25)
- ✅ Arquitetura de 3 camadas
- ✅ Missing value handler
- ✅ Logs detalhados por camada

### v2.5.0 (2026-02-24)
- ✅ Fatores acadêmicos de momentum
- ✅ Fatores VALUE e SIZE
- ✅ Suavização temporal
- ✅ Backtest engine

## 📄 Licença

MIT License

## 👥 Contribuindo

Pull requests são bem-vindos! Para mudanças importantes, abra uma issue primeiro.

## 📧 Contato

- GitHub: [@edipo-dados](https://github.com/edipo-dados)
- Projeto: [quant_stock_rank](https://github.com/edipo-dados/quant_stock_rank)
