"""
Configuração global do yfinance para evitar bloqueios.
Este módulo deve ser importado antes de usar qualquer cliente Yahoo Finance.
"""

import yfinance as yf
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Configurar sessão HTTP robusta
def configure_yfinance():
    """Configura yfinance com sessão HTTP robusta e headers anti-bloqueio."""
    
    # Criar sessão com retry strategy
    session = requests.Session()
    
    # Configurar retry strategy
    retry_strategy = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["HEAD", "GET", "OPTIONS"]
    )
    
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    
    # Headers que imitam um navegador real
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9,pt-BR;q=0.8,pt;q=0.7',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1',
        'Cache-Control': 'max-age=0'
    })
    
    # Aplicar sessão ao yfinance
    yf.utils.get_json = lambda url, proxy=None, timeout=30: session.get(url, proxies=proxy, timeout=timeout).json()
    
    return session

# Configurar automaticamente ao importar este módulo
_session = configure_yfinance()
