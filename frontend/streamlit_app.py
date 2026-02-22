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
    
    Este sistema combina análise fundamentalista e técnica para gerar rankings diários de ações.
    
    **Navegue pelas páginas:**
    - 🏆 Ranking: Visualize o ranking completo
    - 📊 Detalhes do Ativo: Análise detalhada de um ativo específico
    """
)

# Informações sobre a API
st.sidebar.divider()
st.sidebar.caption(f"API Backend: {settings.backend_url}")

# Página principal com instruções
st.markdown("""
## Bem-vindo ao Sistema de Ranking Quantitativo

Este sistema analisa ações brasileiras combinando:

- **Fatores de Momentum**: Retornos históricos, RSI, volatilidade
- **Fatores de Qualidade**: ROE, margens, crescimento de receita
- **Fatores de Valor**: P/L, P/VP, EV/EBITDA

### Como usar:

1. **Página de Ranking** 🏆: Visualize o ranking completo de todos os ativos analisados
2. **Detalhes do Ativo** 📊: Clique em um ativo para ver análise detalhada

### Metodologia:

O sistema calcula scores normalizados para cada categoria de fator e combina-os em um score final ponderado:
- Momentum: 40%
- Qualidade: 30%
- Valor: 30%

Os ativos são então rankeados do maior para o menor score.
""")

# Instruções de navegação
st.info("👈 Use a barra lateral para navegar entre as páginas")
