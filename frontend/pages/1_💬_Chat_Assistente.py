"""
Página de Chat com Assistente IA.

Interface conversacional para análise de ações usando Gemini.
"""

import streamlit as st
import requests
import os
import sys
from datetime import datetime

# Adicionar diretório raiz ao path para imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from app.config import settings

# Configuração da página
st.set_page_config(
    page_title="Chat Assistente - Quant Stock Ranker",
    page_icon="💬",
    layout="wide"
)

# URL da API
API_URL = settings.backend_url

# Inicializar session state
if 'messages' not in st.session_state:
    st.session_state.messages = []

if 'session_id' not in st.session_state:
    st.session_state.session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

if 'gemini_api_key' not in st.session_state:
    # Tentar carregar do ambiente
    default_key = os.getenv('GEMINI_API_KEY', '')
    st.session_state.gemini_api_key = default_key

# Título
st.title("💬 Chat com Assistente IA")

st.markdown("""
Converse com o assistente sobre ações brasileiras! O assistente tem acesso ao sistema de ranking
e pode responder perguntas, fazer análises e comparações.

**Exemplos de perguntas:**
- "Quais são as 5 melhores ações para investir?"
- "Me fale sobre PETR4.SA"
- "Compare VALE3.SA com ITUB4.SA"
- "Quais ações têm momentum forte?"
""")

# Sidebar com configurações
with st.sidebar:
    st.header("⚙️ Configurações")
    
    # API Key do Gemini
    gemini_key = st.text_input(
        "Google Gemini API Key",
        type="password",
        value=st.session_state.gemini_api_key,
        help="Obtenha sua API key em: https://makersuite.google.com/app/apikey"
    )
    
    if gemini_key:
        st.session_state.gemini_api_key = gemini_key
        st.success("✅ API Key configurada")
    else:
        st.warning("⚠️ Configure sua API Key do Gemini")
    
    st.divider()
    
    # Informações da sessão
    st.subheader("📊 Sessão Atual")
    st.text(f"ID: {st.session_state.session_id}")
    st.text(f"Mensagens: {len(st.session_state.messages)}")
    
    # Botão para limpar chat
    if st.button("🗑️ Limpar Chat", use_container_width=True):
        try:
            # Limpar no backend
            response = requests.delete(
                f"{API_URL}/api/v1/chat/session",
                params={"session_id": st.session_state.session_id},
                timeout=10
            )
            
            # Limpar no frontend
            st.session_state.messages = []
            st.rerun()
        except Exception as e:
            st.error(f"Erro ao limpar chat: {e}")
    
    st.divider()
    
    # Dicas
    st.subheader("💡 Dicas")
    st.markdown("""
    - Seja específico nas perguntas
    - Mencione tickers com .SA (ex: PETR4.SA)
    - Peça comparações entre ações
    - Pergunte sobre momentum, qualidade ou valor
    - Solicite análises detalhadas
    """)
    
    st.divider()
    
    # Link para obter API key
    st.markdown("""
    **Não tem API Key?**
    
    [Obter API Key do Gemini →](https://makersuite.google.com/app/apikey)
    
    É grátis para uso pessoal!
    """)

# Área de chat
chat_container = st.container()

# Exibir mensagens
with chat_container:
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

# Input de mensagem
if prompt := st.chat_input("Digite sua mensagem...", disabled=not st.session_state.gemini_api_key):
    if not st.session_state.gemini_api_key:
        st.error("Por favor, configure sua API Key do Gemini na barra lateral.")
    else:
        # Adicionar mensagem do usuário
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Exibir mensagem do usuário
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Obter resposta do assistente
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            message_placeholder.markdown("🤔 Pensando...")
            
            try:
                # Enviar mensagem para API
                response = requests.post(
                    f"{API_URL}/api/v1/chat/message",
                    params={
                        "message": prompt,
                        "session_id": st.session_state.session_id,
                        "gemini_api_key": st.session_state.gemini_api_key
                    },
                    timeout=60
                )
                
                if response.status_code == 200:
                    data = response.json()
                    assistant_response = data["response"]
                    
                    # Exibir resposta
                    message_placeholder.markdown(assistant_response)
                    
                    # Adicionar ao histórico
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": assistant_response
                    })
                else:
                    error_msg = f"Erro {response.status_code}: {response.text}"
                    message_placeholder.error(error_msg)
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": f"❌ {error_msg}"
                    })
            
            except requests.exceptions.Timeout:
                error_msg = "⏱️ Timeout: A requisição demorou muito. Tente novamente."
                message_placeholder.error(error_msg)
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": error_msg
                })
            
            except Exception as e:
                error_msg = f"❌ Erro ao processar mensagem: {str(e)}"
                message_placeholder.error(error_msg)
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": error_msg
                })

# Rodapé
st.divider()
st.caption("""
⚠️ **Aviso Legal**: Este assistente fornece informações baseadas em dados quantitativos.
Não constitui recomendação de investimento. Sempre consulte um profissional qualificado
antes de tomar decisões de investimento.
""")
