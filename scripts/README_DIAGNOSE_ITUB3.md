# Diagnóstico ITUB3 - Por que não aparece no ranking?

## Problema
O ITUB3 não está mais aparecendo no ranking da aplicação, mesmo sendo historicamente top 3.

## Solução - Execute no EC2

### Opção 1: Usando o script auxiliar (mais fácil)

```bash
# No EC2, no diretório do projeto
cd ~/quant_stock_rank
git pull origin main
bash scripts/find_container.sh
```

O script vai mostrar o nome correto do container e o comando para executar.

### Opção 2: Manual

### 1. Conecte no EC2 e encontre o container

```bash
# SSH no EC2
ssh -i sua-chave.pem ubuntu@seu-ec2-ip

# Vá para o diretório do projeto
cd ~/quant_stock_rank

# Atualize o código
git pull origin main

# Encontre o nome do container
bash scripts/find_container.sh

# OU liste manualmente
docker ps

# Entre no container (substitua CONTAINER_NAME pelo nome correto)
docker exec -it CONTAINER_NAME bash
```

**Exemplos de nomes possíveis:**
- `quant_stock_rank-backend-1`
- `backend`
- `quant-backend`
- `app-backend-1`

### 2. Execute o diagnóstico

```bash
# Dentro do container
python scripts/diagnose_itub3.py
```

### 3. Analise o resultado

O script vai verificar:

✅ **ITUB3 existe no banco?**
- Se não: precisa rodar ingestão

✅ **Tem preços recentes?**
- Verifica últimos 60 dias
- Calcula volume médio
- Compara com mínimo (100.000)

✅ **Tem dados fundamentais?**
- Market cap >= 1 bilhão?
- Shareholders equity > 0?
- Revenue > 0?
- Net income >= 0?

✅ **Tem features calculadas?**
- momentum_ex_1m
- roe_mean_3y
- ev_ebitda

✅ **Tem scores calculados?**
- Últimos 5 scores
- Posição no ranking

✅ **Top 10 atual**
- Mostra ranking completo
- Verifica se ITUB3 está presente

## Possíveis Causas e Soluções

### Causa 1: Dados desatualizados
**Sintoma:** Nenhum preço/score nos últimos 60 dias

**Solução:**
```bash
# Rodar pipeline completo
python scripts/run_smart_pipeline.py
```

### Causa 2: Falha nos critérios de elegibilidade
**Sintoma:** is_eligible = False

**Possíveis razões:**
- Market cap < 1 bilhão
- Volume médio < 100.000
- Shareholders equity <= 0
- Revenue <= 0
- Net income negativo

**Solução:** Verificar se os dados fundamentais estão corretos

### Causa 3: Dados fundamentais incorretos
**Sintoma:** Valores None ou zerados

**Solução:**
```bash
# Re-ingerir dados do FMP
python scripts/ingest_fundamentals.py
```

### Causa 4: Features não calculadas
**Sintoma:** Features = None

**Solução:**
```bash
# Recalcular features
python scripts/calculate_features.py
```

### Causa 5: Scores não calculados
**Sintoma:** Nenhum score recente

**Solução:**
```bash
# Recalcular scores
python scripts/calculate_scores.py
```

## Scripts Auxiliares

### Verificar apenas status básico
```bash
python scripts/check_itub3.py
```

### Verificar filtros de elegibilidade
```bash
python scripts/check_eligibility_filters.py
```

## Configurações Importantes

Arquivo: `app/config.py`

```python
minimum_volume: float = 100000  # Volume mínimo diário
minimum_market_cap: float = 1_000_000_000  # 1 bilhão BRL
```

Se ITUB3 não atende esses critérios, não aparecerá no ranking.

## Contato

Se o problema persistir após executar o diagnóstico, compartilhe a saída completa do script.
