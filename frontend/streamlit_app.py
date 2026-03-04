"""
Aplicação Streamlit para visualização de rankings quantitativos.

Entry point principal da aplicação frontend.

Valida: Requisitos 11.1, 11.2, 11.3, 11.4, 11.5, 11.6, 11.7, 11.8
"""

import streamlit as st
import os
import sys

# Adicionar diretório raiz ao path para imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.config import settings

# Configuração da página
st.set_page_config(
    page_title="Quant Stock Ranker",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Título principal
st.title("📈 Sistema de Ranking Quantitativo de Ações")

# Sidebar com informações
st.sidebar.title("Navegação")
st.sidebar.info(
    """
    **Sistema de Ranking Quantitativo**
    
    Análise quantitativa de ações brasileiras usando metodologia acadêmica com 4 fatores:
    
    - **Momentum** (35%): Tendências de preço excluindo curto prazo
    - **Quality** (25%): Rentabilidade e estabilidade financeira
    - **Value** (30%): Múltiplos de valuation e FCF Yield
    - **Size** (10%): Fator de tamanho (size premium)
    
    **Navegue pelas páginas:**
    - 🏆 Ranking: Visualize o ranking completo
    - 📊 Detalhes do Ativo: Análise detalhada
    - 💬 Chat Assistente: Converse sobre os ativos
    - 🔬 Research Backtest: Execute backtests
    """
)

# Informações sobre a API
st.sidebar.divider()
st.sidebar.caption(f"API Backend: {settings.backend_url}")

# Página principal com instruções
st.markdown("""
## Bem-vindo ao Sistema de Ranking Quantitativo

Este sistema analisa ações brasileiras usando metodologia acadêmica baseada em fatores quantitativos:

### 📊 Fatores Analisados

**Momentum (35%)**
- Momentum 6M e 12M excluindo último mês (evita reversão de curto prazo)
- Volatilidade e drawdown recente

**Quality (25%)**
- ROE médio e estabilidade (3 anos)
- Margens líquidas e crescimento de receita
- Alavancagem (Dívida/EBITDA)

**Value (30%)**
- P/L, P/VP, EV/EBITDA
- FCF Yield (Free Cash Flow / Market Cap)

**Size (10%)**
- Fator de tamanho (size premium)
- Empresas menores tendem a ter retornos superiores

### 🎯 Como usar:

1. **Ranking** 🏆: Visualize o ranking completo de todos os ativos analisados
2. **Detalhes do Ativo** 📊: Análise detalhada de um ativo específico
3. **Chat Assistente** 💬: Converse com o assistente sobre os ativos
4. **Research Backtest** 🔬: Execute backtests personalizados com diferentes configurações

### 📊 Funcionalidade de Backtest:

O sistema permite testar estratégias quantitativas em dados históricos (point-in-time) para avaliar performance:

- **Configurações**: Top N ativos (5, 10, 15, 20), ponderação (equal weight ou score weighted)
- **Suavização Temporal**: Reduz turnover usando média exponencial (alpha=0.7)
- **Métricas**: CAGR, Sharpe Ratio, Max Drawdown, Volatilidade, Turnover médio
- **Rebalanceamento**: Mensal (último dia útil do mês)
- **Período**: Dados históricos desde 2021 (mínimo 5 anos recomendado)

### 📈 Metodologia:

O sistema utiliza normalização cross-sectional (z-score) e combina os fatores em um score final ponderado. 
Ativos com dados insuficientes têm seus pesos redistribuídos automaticamente entre os fatores disponíveis.

**Referências acadêmicas**: Jegadeesh & Titman (1993), Fama & French (1992, 1993), Piotroski (2000)
""")

# Instruções de navegação
st.info("👈 Use a barra lateral para navegar entre as páginas")
