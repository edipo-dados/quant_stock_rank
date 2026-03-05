# Guia do Usuário - Modelo Multifator Robusto

## Visão Geral

O sistema agora implementa um modelo multifator robusto inspirado em pesquisa acadêmica (Fama-French, Jegadeesh & Titman, Ang et al., Asness et al.) que combina 4 categorias de fatores:

1. **Momentum** (40%) - Tendências de preço
2. **Value** (30%) - Valuation fundamentalista
3. **Quality** (20%) - Qualidade da empresa
4. **Risk** (10%) - Low Volatility Premium

---

## Novos Fatores Implementados

### Momentum
- ✅ `return_3m` - Retorno de 3 meses
- ✅ `volatility_1y` - Volatilidade anualizada de 1 ano
- ✅ `max_drawdown_1y` - Drawdown máximo de 1 ano

### Quality
- ✅ `roic` - Return on Invested Capital

### Filtros
- ✅ `minimum_market_cap` - Market cap mínimo de 1 bilhão BRL

---

## Novas Visualizações no Dashboard

### 1. Gráfico de Drawdown
Mostra o drawdown do portfólio e benchmark ao longo do tempo.

**Como interpretar:**
- Valores negativos indicam queda desde o pico
- Compare com benchmark para ver proteção em quedas
- Drawdown menor = melhor gestão de risco

### 2. Retornos Anuais
Tabela com retornos por ano e outperformance vs benchmark.

**Como interpretar:**
- Retorno Portfolio: Performance anual da estratégia
- Retorno Benchmark: Performance do IBOVESPA
- Outperformance: Diferença (positivo = bateu o benchmark)

### 3. Gráfico de Turnover
Mostra o turnover (rotatividade) em cada rebalanceamento.

**Como interpretar:**
- Turnover alto (>50%) = muitas mudanças na carteira
- Turnover baixo (<30%) = carteira estável
- Impacta custos de transação

---

## Como Usar

### 1. Validar Dados Antes do Backtest

Sempre valide os dados antes de rodar um backtest:

```bash
# No EC2
docker exec quant-ranker-backend python scripts/validate_backtest_data.py \
  --start-date 2021-01-01 \
  --end-date 2026-03-05 \
  --top-n 10
```

**Saída esperada:**
```
============================================================
VALIDAÇÃO DE DADOS DO BACKTEST
============================================================
Status: ✅ VÁLIDO
Scores disponíveis: 15234
Tickers únicos: 87
Datas únicas: 1245
Benchmark disponível: 1288 registros
============================================================
```

Se houver erros CRITICAL, corrija antes de prosseguir.

### 2. Rodar Pipeline Diário

Para recalcular scores com o novo modelo:

```bash
docker exec quant-ranker-backend python scripts/run_pipeline_docker.py
```

### 3. Executar Backtest

#### Via Frontend (Recomendado)

1. Acesse: `http://seu-ec2-ip:8501`
2. Vá para página "🔬 Research Backtest"
3. Configure:
   - **Nome**: Ex: "Modelo Multifator v2.0"
   - **Data Inicial**: 2021-01-01
   - **Data Final**: 2026-03-05
   - **Top N**: 10 (número de ações)
   - **Capital Inicial**: 100000
   - **Custo de Transação**: 0.003 (0.3%)
4. Clique em "▶️ Executar Backtest"

#### Via Script

```bash
docker exec quant-ranker-backend python scripts/run_backtest_pipeline.py \
  --start-date 2021-01-01 \
  --end-date 2026-03-05 \
  --top-n 10
```

### 4. Analisar Resultados

#### Métricas Principais

**Retorno:**
- Total Return: Retorno total do período
- CAGR: Retorno anualizado composto

**Risco:**
- Volatilidade: Desvio padrão dos retornos
- Max Drawdown: Maior queda desde o pico
- Sharpe Ratio: Retorno ajustado ao risco (>1.0 é bom)
- Sortino Ratio: Similar ao Sharpe, mas penaliza apenas downside
- Calmar Ratio: CAGR / |Max Drawdown| (>1.0 é bom)

**vs Benchmark:**
- Alpha: Retorno excedente vs IBOVESPA (positivo é bom)
- Beta: Sensibilidade ao mercado (1.0 = igual ao mercado)
- Information Ratio: Consistência do alpha (>0.5 é bom)

#### Gráficos

**Equity Curve:**
- Linha azul: Portfólio
- Linha laranja tracejada: Benchmark
- Deve estar acima do benchmark para outperformance

**Drawdown:**
- Área vermelha: Drawdown do portfólio
- Área laranja: Drawdown do benchmark
- Menor área = melhor proteção

**Retornos Anuais:**
- Verde: Anos positivos
- Vermelho: Anos negativos
- Compare com benchmark

**Turnover:**
- Barras azuis: Turnover por rebalance
- Média deve estar <50% para custos controlados

---

## Interpretação de Resultados

### Cenário Ideal
```
Total Return: +150%
CAGR: +25%
Sharpe Ratio: 1.5
Max Drawdown: -15%
Alpha: +10%
Information Ratio: 0.8
Turnover Médio: 35%
```

**Interpretação:**
- ✅ Retorno forte e consistente
- ✅ Risco controlado (drawdown baixo)
- ✅ Sharpe alto = boa relação risco/retorno
- ✅ Alpha positivo = bateu o benchmark
- ✅ IR alto = alpha consistente
- ✅ Turnover moderado = custos controlados

### Cenário Problemático
```
Total Return: +50%
CAGR: +10%
Sharpe Ratio: 0.5
Max Drawdown: -35%
Alpha: -5%
Information Ratio: -0.2
Turnover Médio: 75%
```

**Interpretação:**
- ❌ Retorno fraco
- ❌ Risco alto (drawdown grande)
- ❌ Sharpe baixo = risco não compensado
- ❌ Alpha negativo = perdeu para benchmark
- ❌ IR negativo = alpha inconsistente
- ❌ Turnover alto = custos elevados

**Ações:**
- Revisar filtros de elegibilidade
- Ajustar pesos dos fatores
- Aumentar período de análise
- Verificar qualidade dos dados

---

## Troubleshooting

### Erro: "Validação de dados falhou"

**Causa:** Dados insuficientes no período.

**Solução:**
1. Verificar logs: `docker logs quant-ranker-backend --tail 100`
2. Rodar ingestão: `docker exec quant-ranker-backend python scripts/run_pipeline_docker.py`
3. Validar novamente

### Erro: "Sem scores disponíveis"

**Causa:** Pipeline não rodou ou falhou.

**Solução:**
1. Rodar pipeline: `docker exec quant-ranker-backend python scripts/run_pipeline_docker.py`
2. Verificar logs de erro
3. Verificar se API keys estão configuradas

### Scores aparecem como N/A

**Causa:** Fatores faltantes para alguns ativos.

**Solução:**
- Normal para alguns ativos (ex: bancos não têm EBITDA)
- Sistema usa histórico adaptativo (1-3 anos)
- Ativos com muitos fatores faltantes são excluídos automaticamente

### Backtest muito lento

**Causa:** Muitos dados ou período longo.

**Solução:**
1. Reduzir período (ex: 3 anos ao invés de 5)
2. Reduzir top_n (ex: 10 ao invés de 20)
3. Verificar recursos do EC2

---

## Configurações Avançadas

### Ajustar Pesos dos Fatores

Editar `app/config.py`:

```python
# Pesos padrão (soma = 1.0)
momentum_weight: float = 0.4  # Momentum
quality_weight: float = 0.2   # Quality
value_weight: float = 0.3     # Value
risk_weight: float = 0.1      # Risk
```

**Exemplos:**

**Mais conservador (menos momentum):**
```python
momentum_weight: float = 0.3
quality_weight: float = 0.3
value_weight: float = 0.3
risk_weight: float = 0.1
```

**Mais agressivo (mais momentum):**
```python
momentum_weight: float = 0.5
quality_weight: float = 0.2
value_weight: float = 0.2
risk_weight: float = 0.1
```

Após alterar, rebuild o container:
```bash
docker-compose build backend
docker-compose up -d
```

### Ajustar Filtros de Elegibilidade

Editar `app/config.py`:

```python
# Filtros padrão
minimum_volume: float = 100000  # Volume diário mínimo
minimum_market_cap: float = 1_000_000_000  # 1 bilhão BRL
```

**Mais restritivo (menos ativos):**
```python
minimum_volume: float = 500000  # 500k
minimum_market_cap: float = 5_000_000_000  # 5 bilhões
```

**Menos restritivo (mais ativos):**
```python
minimum_volume: float = 50000  # 50k
minimum_market_cap: float = 500_000_000  # 500 milhões
```

---

## Manutenção

### Backup do Banco de Dados

```bash
# No EC2
cd /path/to/quant-ranker
./deploy/backup-db.sh
```

### Limpar Dados de Backtest Antigos

```bash
docker exec quant-ranker-backend python scripts/clear_backtest_data.py
```

### Atualizar Sistema

```bash
# No EC2
cd /path/to/quant-ranker
git pull origin main
docker-compose down
docker-compose build
docker-compose up -d
```

---

## Referências

### Artigos Acadêmicos
- Fama & French (1993): "Common risk factors in the returns on stocks and bonds"
- Jegadeesh & Titman (1993): "Returns to Buying Winners and Selling Losers"
- Ang et al. (2006): "The Cross-Section of Volatility and Expected Returns"
- Asness et al. (2014): "Quality Minus Junk"

### Documentação Interna
- `docs/MULTIFACTOR_MODEL_PLAN.md` - Plano completo de implementação
- `docs/BACKTEST_IMPROVEMENTS_PLAN.md` - Melhorias do backtest
- `MULTIFACTOR_IMPLEMENTATION_SUMMARY.md` - Resumo técnico das mudanças

---

## Suporte

Para dúvidas ou problemas:

1. Verificar logs: `docker logs quant-ranker-backend --tail 100`
2. Verificar documentação em `docs/`
3. Rodar validação: `scripts/validate_backtest_data.py`
4. Verificar status: `docker ps`

---

**Última atualização:** 2026-03-05
**Versão:** 2.0 (Modelo Multifator Robusto)
