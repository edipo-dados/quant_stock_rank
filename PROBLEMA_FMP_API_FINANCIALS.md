# Problema Crítico: FMP API - Demonstrações Financeiras Indisponíveis

## Resumo do Problema

A API do Financial Modeling Prep (FMP) está em transição entre versões, e as demonstrações financeiras (Income Statement, Balance Sheet, Cash Flow, Key Metrics) **NÃO ESTÃO DISPONÍVEIS** para chaves de API criadas após 31 de agosto de 2025.

## Detalhes Técnicos

### Status Atual da API FMP

1. **API v3 (Legacy)** - `https://financialmodelingprep.com/api/v3`
   - Status: BLOQUEADA para novas chaves de API
   - Erro: "Legacy Endpoint : Due to Legacy endpoints being no longer supported - This endpoint is only available for legacy users who have valid subscriptions prior August 31, 2025"
   - Endpoints afetados:
     - `/income-statement/{ticker}`
     - `/balance-sheet-statement/{ticker}`
     - `/cash-flow-statement/{ticker}`
     - `/key-metrics/{ticker}`

2. **API Stable (Nova)** - `https://financialmodelingprep.com/stable`
   - Status: PARCIALMENTE IMPLEMENTADA
   - Endpoints funcionando:
     - `/search-symbol` ✅
   - Endpoints NÃO DISPONÍVEIS:
     - `/income-statement/{ticker}` ❌ (404)
     - `/balance-sheet-statement/{ticker}` ❌ (404)
     - `/cash-flow-statement/{ticker}` ❌ (404)
     - `/key-metrics/{ticker}` ❌ (404)

### Nossa Situação

- **API Key**: `fNVVAjv4Jlkl7Js2VbCRm7bBivEEQDc3`
- **Status**: Chave criada APÓS 31/08/2025
- **Acesso a v3**: ❌ BLOQUEADO
- **Acesso a /stable**: ✅ PARCIAL (sem demonstrações financeiras)

## Impacto no Sistema

O sistema de ranking quantitativo **DEPENDE** das seguintes demonstrações financeiras:

1. **Income Statement** (Demonstração de Resultados)
   - Necessário para: Revenue, Net Income, Operating Income
   - Usado em: Fatores de qualidade e crescimento

2. **Balance Sheet** (Balanço Patrimonial)
   - Necessário para: Total Assets, Total Debt, Equity
   - Usado em: Fatores de valor (P/B, Debt/Equity)

3. **Cash Flow** (Fluxo de Caixa)
   - Necessário para: Operating Cash Flow, Free Cash Flow
   - Usado em: Fatores de qualidade

4. **Key Metrics** (Métricas Chave)
   - Necessário para: P/E, ROE, ROA, Profit Margins
   - Usado em: Todos os fatores de scoring

**Sem esses dados, o sistema NÃO PODE FUNCIONAR.**

## Soluções Alternativas

### Opção 1: Usar Yahoo Finance (yfinance) ✅ RECOMENDADO

**Vantagens:**
- Gratuito e sem limites de API
- Biblioteca Python bem mantida (`yfinance`)
- Dados confiáveis e atualizados
- Já amplamente usado pela comunidade

**Desvantagens:**
- Não é uma API oficial (scraping)
- Pode ter mudanças sem aviso
- Menos estruturado que FMP

**Implementação:**
```python
import yfinance as yf

# Buscar dados fundamentalistas
ticker = yf.Ticker("AAPL")

# Income Statement
income_stmt = ticker.income_stmt  # Anual
quarterly_income = ticker.quarterly_income_stmt  # Trimestral

# Balance Sheet
balance_sheet = ticker.balance_sheet  # Anual
quarterly_balance = ticker.quarterly_balance_sheet  # Trimestral

# Cash Flow
cash_flow = ticker.cashflow  # Anual
quarterly_cashflow = ticker.quarterly_cashflow  # Trimestral

# Informações gerais e métricas
info = ticker.info  # Contém P/E, Market Cap, etc.
```

### Opção 2: Alpha Vantage API

**Vantagens:**
- API oficial e estável
- Plano gratuito disponível (500 chamadas/dia)
- Bem documentada

**Desvantagens:**
- Limite de chamadas no plano gratuito
- Requer chave de API
- Menos dados que FMP

**Website:** https://www.alphavantage.co/

### Opção 3: Polygon.io

**Vantagens:**
- API moderna e bem documentada
- Dados de alta qualidade
- Plano gratuito disponível

**Desvantagens:**
- Limites no plano gratuito
- Foco em dados de mercado (preços)
- Dados fundamentalistas limitados no plano gratuito

**Website:** https://polygon.io/

### Opção 4: Aguardar FMP Migrar Endpoints

**Vantagens:**
- Mantém a implementação atual
- FMP tem boa documentação

**Desvantagens:**
- Não há prazo definido para migração
- Sistema fica inoperante até lá
- Incerteza sobre quando será resolvido

## Recomendação

**MIGRAR PARA YAHOO FINANCE (yfinance)** imediatamente:

1. É gratuito e funcional
2. Tem todos os dados necessários
3. Implementação simples
4. Amplamente usado e testado
5. Não depende de chaves de API

## Próximos Passos

1. Instalar yfinance: `pip install yfinance`
2. Criar novo cliente `YahooFinanceClient` similar ao `FMPClient`
3. Atualizar `ingestion_service.py` para usar Yahoo Finance
4. Testar extração de dados
5. Atualizar testes unitários
6. Documentar mudança

## Referências

- Documentação FMP: https://site.financialmodelingprep.com/developer/docs
- Documentação yfinance: https://github.com/ranaroussi/yfinance
- Alpha Vantage: https://www.alphavantage.co/documentation/
- Polygon.io: https://polygon.io/docs/stocks/getting-started

## Data do Problema

- Identificado em: 18 de fevereiro de 2026
- Última tentativa de solução: 18 de fevereiro de 2026
- Status: BLOQUEADO pela FMP (endpoints não disponíveis para novas chaves)
