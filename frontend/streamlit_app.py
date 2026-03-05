"""
Aplicação Streamlit para visualização de rankings quantitativos.

Entry point principal da aplicação frontend.
Redireciona para a página Sobre.

Valida: Requisitos 11.1, 11.2, 11.3, 11.4, 11.5, 11.6, 11.7, 11.8
"""

import streamlit as st

# Configuração da página
st.set_page_config(
    page_title="Quant Stock Ranker",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Redirecionar para a página Sobre
st.switch_page("pages/0_ℹ️_Sobre.py")
