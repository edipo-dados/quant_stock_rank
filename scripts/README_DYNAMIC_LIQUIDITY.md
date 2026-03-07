# Seleção Dinâmica de Ações por Liquidez

## Problema Resolvido

Antes: Lista fixa de ações no código (`B3_UNIVERSE`)
- Ações podiam perder liquidez e continuar na lista
- Novas ações líquidas não eram incluídas automaticamente
- ITUB3 e outras blue chips podiam ser excluídas por erro

Agora: Seleção dinâmica baseada em liquidez real
- Busca automaticamente as ações mais líquidas
- Atualiza lista baseado em volume financeiro real
- Garante que blue chips como ITUB3 sempre estejam incluídas

## Como Funciona

### 1. Universo de Candidatos

O sistema combina múltiplas fontes:
- Lista base `B3_UNIVERSE` (ações conhecidas)
- Componentes do Ibovespa (quando disponível via API)
- Filtro por liquidez real (volume financeiro)

### 2. Critérios de Liquidez

```python
lookback_days = 30  # Últimos 30 dias
min_volume = 1_000_000.0  # R$ 1 milhão/dia mínimo
```

Cálculo:
- Volume financeiro = Volume de ações × Preço de fechamento
- Média dos últimos 30 dias
- Ordenação por liquidez (maior primeiro)

### 3. Atualização Automática

O script `update_liquid_stocks.py`:
1. Busca top N ações mais líquidas
2. Adiciona novas ações ao banco
3. Reativa ações que voltaram a ser líquidas
4. Desativa ações que perderam liquidez

## Scripts Disponíveis

### Testar Busca de Liquidez

```bash
# Local (Windows)
python scripts/test_liquid_stocks.py

# EC2 (Docker)
docker exec -it quant-ranker-backend python scripts/test_liquid_stocks.py
```

Mostra:
- Top 50 ações mais líquidas
- Volume financeiro médio
- Posição do ITUB3 no ranking
- Comparação entre universo dinâmico e lista fixa

### Atualizar Lista no Banco

```bash
# Local (Windows)
python scripts/update_liquid_stocks.py

# EC2 (Docker)
docker exec -it quant-ranker-backend python scripts/update_liquid_stocks.py

# Com parâmetros customizados
python scripts/update_liquid_stocks.py --limit 150 --days 60 --min-volume 2000000
```

Parâmetros:
- `--limit`: Número máximo de ações (default: 100)
- `--days`: Dias para calcular liquidez (default: 30)
- `--min-volume`: Volume mínimo em R$ (default: 1.000.000)
- `--no-dynamic`: Usar apenas lista fixa

## Integração com Pipeline

### Opção 1: Manual (Recomendado inicialmente)

```bash
# 1. Atualizar lista de ações líquidas
docker exec -it quant-ranker-backend python scripts/update_liquid_stocks.py

# 2. Rodar pipeline completo
docker exec -it quant-ranker-backend python scripts/run_smart_pipeline.py
```

### Opção 2: Automático (Futuro)

Adicionar ao cron job:
```bash
# Atualizar liquidez semanalmente (domingo 2h)
0 2 * * 0 docker exec quant-ranker-backend python scripts/update_liquid_stocks.py

# Pipeline diário continua normal
0 3 * * * docker exec quant-ranker-backend python scripts/run_smart_pipeline.py
```

## Vantagens

### 1. Sempre Atualizado
- Ações líquidas são detectadas automaticamente
- Blue chips como ITUB3 sempre incluídas
- Ações que perdem liquidez são removidas

### 2. Baseado em Dados Reais
- Volume financeiro real dos últimos 30 dias
- Não depende de lista manual
- Adapta-se a mudanças no mercado

### 3. Flexível
- Parâmetros configuráveis (limite, dias, volume mínimo)
- Pode usar universo dinâmico ou lista fixa
- Fácil de testar antes de aplicar

## Verificação

### Verificar ITUB3 está na lista

```bash
docker exec -it quant-ranker-backend python -c "
from app.models.database import SessionLocal
from app.models.schemas import AssetInfo

db = SessionLocal()
itub3 = db.query(AssetInfo).filter(AssetInfo.ticker == 'ITUB3').first()

if itub3:
    print(f'✓ ITUB3 encontrado')
    print(f'  is_active: {itub3.is_active}')
    print(f'  is_eligible: {itub3.is_eligible}')
else:
    print('❌ ITUB3 não encontrado')

db.close()
"
```

### Ver todas as ações ativas

```bash
docker exec -it quant-ranker-backend python -c "
from app.models.database import SessionLocal
from app.models.schemas import AssetInfo

db = SessionLocal()
assets = db.query(AssetInfo).filter(AssetInfo.is_active == True).all()

print(f'Total de ativos ativos: {len(assets)}')
print('Tickers:', [a.ticker for a in assets])

db.close()
"
```

## Troubleshooting

### ITUB3 não aparece após atualização

1. Verificar se está na lista líquida:
```bash
docker exec -it quant-ranker-backend python scripts/test_liquid_stocks.py | grep ITUB3
```

2. Se não está, verificar volume:
```bash
# Reduzir volume mínimo temporariamente
docker exec -it quant-ranker-backend python scripts/update_liquid_stocks.py --min-volume 500000
```

3. Forçar inclusão manual se necessário:
```bash
docker exec -it quant-ranker-backend python -c "
from app.models.database import SessionLocal
from app.models.schemas import AssetInfo
from datetime import datetime

db = SessionLocal()
itub3 = db.query(AssetInfo).filter(AssetInfo.ticker == 'ITUB3').first()

if not itub3:
    itub3 = AssetInfo(
        ticker='ITUB3',
        name='Itaú Unibanco',
        is_active=True,
        is_eligible=True,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    db.add(itub3)
else:
    itub3.is_active = True
    itub3.updated_at = datetime.now()

db.commit()
print('✓ ITUB3 ativado')
db.close()
"
```

## Próximos Passos

1. Testar localmente: `python scripts/test_liquid_stocks.py`
2. Atualizar no EC2: `docker exec -it quant-ranker-backend python scripts/update_liquid_stocks.py`
3. Verificar ITUB3: `docker exec -it quant-ranker-backend python scripts/diagnose_itub3.py`
4. Rodar pipeline: `docker exec -it quant-ranker-backend python scripts/run_smart_pipeline.py`
