# Guia de Migração: Melhorias do Modelo de Scoring

Este documento descreve as mudanças introduzidas pelas melhorias do modelo de scoring e fornece instruções para migração de sistemas existentes.

## Visão Geral das Mudanças

As melhorias transformam o modelo de scoring de um sistema puramente matemático em um sistema economicamente robusto que:

1. **Filtra ativos financeiramente distressed** antes do scoring
2. **Usa cálculos robustos** para o fator de qualidade (ROE com média de 3 anos, winsorização, penalidades de alavancagem)
3. **Trata outliers sistematicamente** com winsorização antes da normalização
4. **Penaliza riscos extremos** (volatilidade e drawdown excessivos)
5. **Fornece transparência completa** com breakdown detalhado de scores e penalidades

## Mudanças no Banco de Dados

### Novas Colunas na Tabela `scores_daily`

A tabela `scores_daily` foi estendida com as seguintes colunas:

| Coluna | Tipo | Descrição | Padrão |
|--------|------|-----------|--------|
| `base_score` | Float | Score antes das penalidades de risco | NULL |
| `risk_penalty_factor` | Float | Fator de penalidade combinado (0-1] | NULL |
| `passed_eligibility` | Boolean | Se o ativo passou no filtro de elegibilidade | TRUE |
| `exclusion_reasons` | JSON | Lista de razões de exclusão (se aplicável) | NULL |
| `risk_penalties` | JSON | Breakdown de penalidades individuais | NULL |

### Script de Migração

Execute o script de migração para adicionar as novas colunas:

```bash
python scripts/migrate_score_schema.py
```

O script:
- Adiciona as novas colunas à tabela existente
- Define valores padrão para registros existentes
- Não remove dados existentes
- É idempotente (pode ser executado múltiplas vezes)

**Importante:** Faça backup do banco de dados antes de executar a migração!

```bash
# Backup do banco (exemplo com Docker)
docker exec quant_ranker_db pg_dump -U user quant_ranker > backup_$(date +%Y%m%d).sql
```

## Mudanças na Configuração

### Novas Variáveis de Ambiente

Adicione as seguintes variáveis ao seu arquivo `.env`:

```bash
# Filtro de Elegibilidade
MINIMUM_VOLUME=100000          # Volume médio diário mínimo

# Parâmetros de Qualidade Robusta
MAX_ROE_LIMIT=0.50            # Cap de ROE em 50%
DEBT_EBITDA_LIMIT=4.0         # Limite de dívida/EBITDA

# Penalização de Risco
VOLATILITY_LIMIT=0.60         # Limite de volatilidade (60%)
DRAWDOWN_LIMIT=-0.50          # Limite de drawdown (-50%)

# Winsorização
WINSORIZE_LOWER_PCT=0.05      # Percentil inferior (5%)
WINSORIZE_UPPER_PCT=0.95      # Percentil superior (95%)
```

**Valores Padrão:** Se não especificadas, o sistema usa os valores padrão acima.

### Atualização do .env

1. Copie as novas variáveis de `.env.example` para seu `.env`
2. Ajuste os valores conforme sua estratégia
3. Reinicie o backend para aplicar as mudanças

## Mudanças na API

### Novos Campos nas Respostas

Todos os endpoints que retornam scores agora incluem campos adicionais:

#### Endpoint `/ranking`

**Antes:**
```json
{
  "ticker": "PETR4",
  "final_score": 1.85,
  "momentum_score": 2.1,
  "quality_score": 1.5,
  "value_score": 1.9,
  "confidence": 0.5,
  "rank": 1
}
```

**Depois:**
```json
{
  "ticker": "PETR4",
  "final_score": 1.48,
  "base_score": 1.85,
  "momentum_score": 2.1,
  "quality_score": 1.5,
  "value_score": 1.9,
  "confidence": 0.5,
  "rank": 1,
  "passed_eligibility": true,
  "exclusion_reasons": [],
  "risk_penalties": {
    "volatility": 1.0,
    "drawdown": 0.8
  },
  "penalty_factor": 0.8
}
```

#### Endpoint `/asset/{ticker}`

**Antes:**
```json
{
  "ticker": "PETR4",
  "score": {
    "final_score": 1.85,
    ...
  },
  "explanation": "...",
  "raw_factors": {...}
}
```

**Depois:**
```json
{
  "ticker": "PETR4",
  "score": {
    "final_score": 1.48,
    "base_score": 1.85,
    "passed_eligibility": true,
    "exclusion_reasons": [],
    "risk_penalties": {
      "volatility": 1.0,
      "drawdown": 0.8
    },
    "penalty_factor": 0.8,
    ...
  },
  "explanation": "...",
  "raw_factors": {...}
}
```

#### Endpoint `/top`

Mesmas mudanças do endpoint `/ranking`.

### Compatibilidade com Clientes Existentes

**Campos Antigos:** Todos os campos existentes são mantidos, garantindo compatibilidade retroativa.

**Novos Campos:** Clientes que não esperam os novos campos podem simplesmente ignorá-los.

**Recomendação:** Atualize seus clientes para consumir os novos campos e fornecer transparência aos usuários.

## Mudanças no Comportamento

### 1. Filtro de Elegibilidade

**Antes:** Todos os ativos eram incluídos no cálculo de scores.

**Depois:** Ativos são filtrados antes do scoring se:
- Patrimônio líquido ≤ 0
- EBITDA ≤ 0
- Receita ≤ 0
- Volume médio diário < `MINIMUM_VOLUME`

**Impacto:** Ativos excluídos ainda aparecem nas respostas da API com `passed_eligibility=false` e `exclusion_reasons` preenchido.

### 2. Cálculo de ROE Robusto

**Antes:** ROE calculado com dados de um único período.

**Depois:** ROE calculado como:
1. Média dos últimos 3 anos
2. Com winsorização nos percentis 5% e 95%
3. Com cap em 50% (configurável)

**Impacto:** ROE mais estável e resistente a distorções contábeis.

### 3. Fator de Qualidade Aprimorado

**Antes:** Qualidade baseada apenas em ROE, margens e crescimento.

**Depois:** Qualidade inclui:
- ROE robusto (30%)
- Margem líquida (25%)
- Crescimento de receita (20%)
- Força financeira baseada em dívida/EBITDA (15%)
- Estabilidade do lucro líquido (10%)

**Impacto:** Empresas com alta alavancagem ou lucros voláteis recebem scores de qualidade menores.

### 4. Winsorização Sistemática

**Antes:** Outliers não eram tratados antes da normalização.

**Depois:** Todos os fatores são winsorized nos percentis 5% e 95% antes do z-score.

**Impacto:** Normalização mais robusta, menos influenciada por valores extremos.

### 5. Penalização de Risco

**Antes:** Scores finais não consideravam risco extremo.

**Depois:** Scores são penalizados se:
- Volatilidade 180d > `VOLATILITY_LIMIT` → penalidade de 0.8
- Drawdown 3y < `DRAWDOWN_LIMIT` → penalidade de 0.8
- Penalidades são multiplicativas

**Impacto:** Ativos com risco extremo recebem scores finais menores, mesmo com bons fundamentos.

**Exemplo:**
```
base_score = 2.0
volatility_penalty = 0.8 (volatilidade alta)
drawdown_penalty = 0.8 (drawdown severo)
final_score = 2.0 × 0.8 × 0.8 = 1.28
```

## Exemplos de Migração

### Exemplo 1: Cliente Python Consumindo a API

**Antes:**
```python
import requests

response = requests.get("http://localhost:8000/ranking")
data = response.json()

for asset in data["rankings"]:
    print(f"{asset['ticker']}: {asset['final_score']:.2f}")
```

**Depois (com novos campos):**
```python
import requests

response = requests.get("http://localhost:8000/ranking")
data = response.json()

for asset in data["rankings"]:
    ticker = asset['ticker']
    final_score = asset['final_score']
    base_score = asset.get('base_score', final_score)  # Fallback para compatibilidade
    penalty = asset.get('penalty_factor', 1.0)
    
    print(f"{ticker}: {final_score:.2f} (base: {base_score:.2f}, penalty: {penalty:.2f})")
    
    if not asset.get('passed_eligibility', True):
        reasons = ', '.join(asset.get('exclusion_reasons', []))
        print(f"  ⚠️ Excluído: {reasons}")
```

### Exemplo 2: Frontend Streamlit

**Antes:**
```python
import streamlit as st
import requests

response = requests.get("http://localhost:8000/ranking")
rankings = response.json()["rankings"]

st.dataframe(rankings)
```

**Depois (com breakdown de penalidades):**
```python
import streamlit as st
import requests
import pandas as pd

response = requests.get("http://localhost:8000/ranking")
rankings = response.json()["rankings"]

# Criar DataFrame com novos campos
df = pd.DataFrame(rankings)

# Adicionar coluna de status
df['status'] = df['passed_eligibility'].apply(
    lambda x: '✅ Elegível' if x else '❌ Excluído'
)

# Adicionar coluna de penalidades
df['penalties'] = df.apply(
    lambda row: ', '.join([
        f"{k}: {v:.2f}" 
        for k, v in row.get('risk_penalties', {}).items() 
        if v < 1.0
    ]) or 'Nenhuma',
    axis=1
)

# Exibir
st.dataframe(df[[
    'rank', 'ticker', 'final_score', 'base_score', 
    'status', 'penalties'
]])
```

## Checklist de Migração

### Pré-Migração

- [ ] Fazer backup completo do banco de dados
- [ ] Revisar e documentar configurações atuais
- [ ] Testar script de migração em ambiente de desenvolvimento
- [ ] Atualizar dependências Python (se necessário)

### Migração do Banco de Dados

- [ ] Executar `python scripts/migrate_score_schema.py`
- [ ] Verificar que novas colunas foram criadas
- [ ] Confirmar que dados existentes não foram perdidos
- [ ] Testar queries com novos campos

### Atualização de Configuração

- [ ] Adicionar novas variáveis ao `.env`
- [ ] Revisar e ajustar valores conforme estratégia
- [ ] Validar configuração com `python -c "from app.config import settings; print(settings)"`

### Atualização de Código

- [ ] Atualizar clientes da API para consumir novos campos
- [ ] Atualizar frontend para exibir breakdown de penalidades
- [ ] Atualizar dashboards e relatórios
- [ ] Atualizar testes automatizados

### Validação

- [ ] Executar suite completa de testes: `pytest tests/ -v`
- [ ] Testar endpoints da API manualmente
- [ ] Verificar que scores são calculados corretamente
- [ ] Confirmar que filtro de elegibilidade funciona
- [ ] Validar que penalidades são aplicadas corretamente

### Pós-Migração

- [ ] Monitorar logs por erros
- [ ] Comparar scores antigos vs novos (esperado: diferenças)
- [ ] Documentar mudanças observadas
- [ ] Comunicar mudanças aos usuários finais

## Rollback

Se necessário reverter as mudanças:

### 1. Restaurar Banco de Dados

```bash
# Restaurar do backup
docker exec -i quant_ranker_db psql -U user quant_ranker < backup_YYYYMMDD.sql
```

### 2. Reverter Código

```bash
# Voltar para commit anterior
git checkout <commit-hash-anterior>

# Ou reverter merge
git revert <merge-commit-hash>
```

### 3. Restaurar Configuração

```bash
# Remover novas variáveis do .env
# Ou restaurar .env do backup
```

## Perguntas Frequentes

### Os scores vão mudar após a migração?

**Sim.** Os scores serão diferentes devido a:
- Filtro de elegibilidade excluindo ativos distressed
- Cálculo robusto de ROE (média de 3 anos)
- Winsorização de outliers
- Penalidades de risco

Isso é esperado e desejado - os novos scores são mais robustos economicamente.

### Ativos podem desaparecer do ranking?

**Não.** Ativos excluídos pelo filtro de elegibilidade ainda aparecem nas respostas da API, mas com `passed_eligibility=false` e `exclusion_reasons` preenchido.

### Preciso atualizar meus clientes da API?

**Não obrigatório.** A API mantém compatibilidade retroativa - todos os campos antigos continuam presentes. Porém, é recomendado atualizar para aproveitar os novos campos e fornecer transparência.

### Como ajustar os parâmetros de penalização?

Edite as variáveis no `.env`:
- `VOLATILITY_LIMIT`: Aumente para ser mais tolerante a volatilidade
- `DRAWDOWN_LIMIT`: Torne mais negativo para ser mais tolerante a drawdowns
- `DEBT_EBITDA_LIMIT`: Aumente para ser mais tolerante a alavancagem

### Os testes ainda passam?

**Sim.** Execute `pytest tests/ -v` para confirmar. Todos os 254 testes devem passar.

## Suporte

Para dúvidas ou problemas durante a migração:

1. Consulte este guia
2. Revise os logs do sistema
3. Execute os testes: `pytest tests/ -v`
4. Verifique a documentação técnica em `.kiro/specs/scoring-model-improvements/`
5. Entre em contato com a equipe de desenvolvimento

---

**Última atualização:** 2024-01-15
**Versão:** 1.0.0
