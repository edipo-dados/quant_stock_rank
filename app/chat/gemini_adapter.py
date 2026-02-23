"""
Adaptador para integrar Gemini com as ferramentas do sistema de ranking.

Permite que o Gemini acesse dados de ranking através de function calling.
"""

import json
import logging
from typing import Any, Dict, List, Optional
from datetime import date, datetime, timedelta
from google import genai
from google.genai import types
from sqlalchemy.orm import Session
import requests

logger = logging.getLogger(__name__)


def _serialize_dates(obj):
    """Converte objetos date para string ISO format e sanitiza valores inválidos."""
    import math
    
    # Tratar NaN, Infinity
    if isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            return None
        return obj
    elif isinstance(obj, date):
        return obj.isoformat()
    elif isinstance(obj, dict):
        return {k: _serialize_dates(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_serialize_dates(item) for item in obj]
    return obj


class GeminiChatAdapter:
    """Adaptador para chat com Gemini usando ferramentas do sistema."""
    
    def __init__(self, api_key: str, db: Session):
        """
        Inicializa o adaptador Gemini.
        
        Args:
            api_key: API key do Google Gemini
            db: Sessão do banco de dados
        """
        self.client = genai.Client(api_key=api_key)
        self.db = db
        self.chat = None
        self.model_name = 'gemini-2.5-flash'
    
    def _create_tools(self) -> List[types.Tool]:
        """Cria definições de ferramentas para o Gemini."""
        return [
            types.Tool(
                function_declarations=[
                    types.FunctionDeclaration(
                        name="get_ranking",
                        description="Obtém o ranking completo de ações ordenado por score final. Retorna lista de ativos com scores de momentum, qualidade e valor.",
                        parameters=types.Schema(
                            type=types.Type.OBJECT,
                            properties={
                                "limit": types.Schema(
                                    type=types.Type.INTEGER,
                                    description="Número máximo de ativos a retornar (opcional, padrão: todos)"
                                )
                            }
                        )
                    ),
                    types.FunctionDeclaration(
                        name="get_top_stocks",
                        description="Obtém os top N ativos com maior score final. Útil para identificar as melhores oportunidades de investimento.",
                        parameters=types.Schema(
                            type=types.Type.OBJECT,
                            properties={
                                "n": types.Schema(
                                    type=types.Type.INTEGER,
                                    description="Número de ativos a retornar (padrão: 10, máximo: 100)"
                                )
                            }
                        )
                    ),
                    types.FunctionDeclaration(
                        name="get_asset_details",
                        description="Obtém detalhes completos de um ativo específico incluindo score, breakdown por fator, posição no ranking e explicação automática.",
                        parameters=types.Schema(
                            type=types.Type.OBJECT,
                            properties={
                                "ticker": types.Schema(
                                    type=types.Type.STRING,
                                    description="Símbolo do ativo (ex: PETR4.SA, VALE3.SA, ITUB4.SA)"
                                )
                            },
                            required=["ticker"]
                        )
                    ),
                    types.FunctionDeclaration(
                        name="get_price_history",
                        description="Obtém histórico de preços diários de um ativo. Retorna dados de open, high, low, close, volume.",
                        parameters=types.Schema(
                            type=types.Type.OBJECT,
                            properties={
                                "ticker": types.Schema(
                                    type=types.Type.STRING,
                                    description="Símbolo do ativo (ex: PETR4.SA)"
                                ),
                                "days": types.Schema(
                                    type=types.Type.INTEGER,
                                    description="Número de dias de histórico (padrão: 30, máximo: 365)"
                                )
                            },
                            required=["ticker"]
                        )
                    ),
                    types.FunctionDeclaration(
                        name="compare_assets",
                        description="Compara múltiplos ativos lado a lado mostrando seus scores e posições no ranking.",
                        parameters=types.Schema(
                            type=types.Type.OBJECT,
                            properties={
                                "tickers": types.Schema(
                                    type=types.Type.ARRAY,
                                    items=types.Schema(type=types.Type.STRING),
                                    description="Lista de tickers para comparar (ex: ['PETR4.SA', 'VALE3.SA'])"
                                )
                            },
                            required=["tickers"]
                        )
                    ),
                    types.FunctionDeclaration(
                        name="search_by_criteria",
                        description="Busca ativos que atendem critérios específicos de score. Útil para filtrar ações por momentum, qualidade ou valor.",
                        parameters=types.Schema(
                            type=types.Type.OBJECT,
                            properties={
                                "min_momentum": types.Schema(
                                    type=types.Type.NUMBER,
                                    description="Score mínimo de momentum (-1 a 1)"
                                ),
                                "min_quality": types.Schema(
                                    type=types.Type.NUMBER,
                                    description="Score mínimo de qualidade (-1 a 1)"
                                ),
                                "min_value": types.Schema(
                                    type=types.Type.NUMBER,
                                    description="Score mínimo de valor (-1 a 1)"
                                ),
                                "max_results": types.Schema(
                                    type=types.Type.INTEGER,
                                    description="Número máximo de resultados (padrão: 10)"
                                )
                            }
                        )
                    ),
                    types.FunctionDeclaration(
                        name="search_company_news",
                        description="Busca notícias recentes sobre uma empresa na web. Útil para entender contexto atual, eventos recentes e sentimento do mercado.",
                        parameters=types.Schema(
                            type=types.Type.OBJECT,
                            properties={
                                "ticker": types.Schema(
                                    type=types.Type.STRING,
                                    description="Símbolo do ativo (ex: PETR4.SA)"
                                ),
                                "days": types.Schema(
                                    type=types.Type.INTEGER,
                                    description="Número de dias para buscar notícias (padrão: 7)"
                                )
                            },
                            required=["ticker"]
                        )
                    ),
                    types.FunctionDeclaration(
                        name="web_search",
                        description="Faz uma busca na web sobre qualquer tópico. Use para buscar notícias, análises, opiniões de especialistas sobre empresas e mercado.",
                        parameters=types.Schema(
                            type=types.Type.OBJECT,
                            properties={
                                "query": types.Schema(
                                    type=types.Type.STRING,
                                    description="Termo de busca (ex: 'PRIO3 notícias 2026', 'análise Petrobras especialistas')"
                                ),
                                "num_results": types.Schema(
                                    type=types.Type.INTEGER,
                                    description="Número de resultados (padrão: 5, máximo: 10)"
                                )
                            },
                            required=["query"]
                        )
                    ),
                    types.FunctionDeclaration(
                        name="get_company_info",
                        description="Obtém informações fundamentais da empresa: setor, descrição do negócio, principais produtos/serviços.",
                        parameters=types.Schema(
                            type=types.Type.OBJECT,
                            properties={
                                "ticker": types.Schema(
                                    type=types.Type.STRING,
                                    description="Símbolo do ativo (ex: PETR4.SA)"
                                )
                            },
                            required=["ticker"]
                        )
                    ),
                    types.FunctionDeclaration(
                        name="get_market_context",
                        description="Obtém contexto do mercado brasileiro: índice Ibovespa, dólar, juros Selic, sentimento geral.",
                        parameters=types.Schema(
                            type=types.Type.OBJECT,
                            properties={}
                        )
                    )
                ]
            )
        ]
    
    async def _execute_function(self, function_name: str, args: Dict[str, Any]) -> Dict:
        """
        Executa uma função do sistema.
        
        Args:
            function_name: Nome da função
            args: Argumentos da função
            
        Returns:
            Resultado da função
        """
        # Import here to avoid circular dependency
        from app.api.routes import (
            get_ranking,
            get_top_assets,
            get_asset_detail,
            get_price_history
        )
        
        try:
            if function_name == "get_ranking":
                result = await get_ranking(
                    date=None,
                    db=self.db
                )
                # Aplicar limite se fornecido
                if "limit" in args:
                    result.rankings = result.rankings[:args["limit"]]
                    result.total_assets = len(result.rankings)
                return _serialize_dates(result.dict())
            
            elif function_name == "get_top_stocks":
                n = args.get("n", 10)
                result = await get_top_assets(
                    n=n,
                    date=None,
                    db=self.db
                )
                return _serialize_dates(result.dict())
            
            elif function_name == "get_asset_details":
                ticker = args["ticker"].upper()
                result = await get_asset_detail(
                    ticker=ticker,
                    date=None,
                    db=self.db
                )
                return _serialize_dates(result.dict())
            
            elif function_name == "get_price_history":
                ticker = args["ticker"].upper()
                days = args.get("days", 30)
                result = await get_price_history(
                    ticker=ticker,
                    days=days,
                    db=self.db
                )
                return _serialize_dates(result)
            
            elif function_name == "compare_assets":
                tickers = [t.upper() for t in args["tickers"]]
                comparisons = []
                
                for ticker in tickers:
                    try:
                        result = await get_asset_detail(
                            ticker=ticker,
                            date=None,
                            db=self.db
                        )
                        asset_data = result.dict()
                        comparisons.append({
                            "ticker": ticker,
                            "final_score": asset_data["score"]["final_score"],
                            "rank": asset_data["score"]["rank"],
                            "momentum_score": asset_data["score"]["momentum_score"],
                            "quality_score": asset_data["score"]["quality_score"],
                            "value_score": asset_data["score"]["value_score"],
                        })
                    except Exception as e:
                        comparisons.append({
                            "ticker": ticker,
                            "error": str(e)
                        })
                
                return _serialize_dates({"comparison": comparisons})
            
            elif function_name == "search_by_criteria":
                # Obter ranking completo
                result = await get_ranking(date=None, db=self.db)
                rankings = result.dict()["rankings"]
                
                # Filtrar por critérios
                filtered = []
                for asset in rankings:
                    if "min_momentum" in args and asset["momentum_score"] < args["min_momentum"]:
                        continue
                    if "min_quality" in args and asset["quality_score"] < args["min_quality"]:
                        continue
                    if "min_value" in args and asset["value_score"] < args["min_value"]:
                        continue
                    
                    filtered.append(asset)
                
                # Aplicar limite
                max_results = args.get("max_results", 10)
                filtered = filtered[:max_results]
                
                return _serialize_dates({
                    "total_found": len(filtered),
                    "results": filtered
                })
            
            elif function_name == "search_company_news":
                ticker = args["ticker"].upper()
                days = args.get("days", 7)
                
                # Extrair nome da empresa do ticker
                company_name = ticker.replace(".SA", "")
                
                # Fazer busca web sobre a empresa
                search_query = f"{company_name} ações notícias {datetime.now().year}"
                
                try:
                    from duckduckgo_search import DDGS
                    
                    results = []
                    with DDGS() as ddgs:
                        search_results = list(ddgs.text(search_query, max_results=5))
                        
                        for r in search_results:
                            results.append({
                                "title": r.get("title", ""),
                                "snippet": r.get("body", ""),
                                "url": r.get("href", ""),
                                "source": r.get("href", "").split("/")[2] if r.get("href") else ""
                            })
                    
                    return {
                        "ticker": ticker,
                        "company": company_name,
                        "query": search_query,
                        "results_count": len(results),
                        "results": results
                    }
                except ImportError:
                    # Fallback se duckduckgo_search não estiver instalado
                    return {
                        "ticker": ticker,
                        "company": company_name,
                        "message": "Módulo de busca não instalado. Instale: pip install duckduckgo-search",
                        "suggestion": "Verifique sites como InfoMoney, Valor Econômico, e relatórios de RI da empresa."
                    }
                except Exception as e:
                    return {"error": f"Erro ao buscar notícias: {str(e)}"}
            
            elif function_name == "web_search":
                query = args["query"]
                num_results = min(args.get("num_results", 5), 10)
                
                try:
                    from duckduckgo_search import DDGS
                    
                    results = []
                    with DDGS() as ddgs:
                        search_results = list(ddgs.text(query, max_results=num_results))
                        
                        for r in search_results:
                            results.append({
                                "title": r.get("title", ""),
                                "snippet": r.get("body", ""),
                                "url": r.get("href", ""),
                                "source": r.get("href", "").split("/")[2] if r.get("href") else ""
                            })
                    
                    return {
                        "query": query,
                        "results_count": len(results),
                        "results": results
                    }
                except ImportError:
                    return {
                        "error": "Módulo de busca não instalado",
                        "message": "Para habilitar busca web, instale: pip install duckduckgo-search"
                    }
                except Exception as e:
                    return {"error": f"Erro na busca: {str(e)}"}
            
            elif function_name == "get_company_info":
                ticker = args["ticker"].upper()
                
                try:
                    # Buscar informações da empresa via yfinance
                    import yfinance as yf
                    
                    stock = yf.Ticker(ticker)
                    info = stock.info
                    
                    result = {
                        "ticker": ticker,
                        "name": info.get("longName", "N/A"),
                        "sector": info.get("sector", "N/A"),
                        "industry": info.get("industry", "N/A"),
                        "description": info.get("longBusinessSummary", "N/A")[:500] + "..." if info.get("longBusinessSummary") else "N/A",
                        "website": info.get("website", "N/A"),
                        "employees": info.get("fullTimeEmployees", "N/A"),
                        "market_cap": info.get("marketCap", "N/A"),
                        "country": info.get("country", "N/A")
                    }
                    
                    return _serialize_dates(result)
                except Exception as e:
                    return {"error": f"Erro ao buscar informações da empresa: {str(e)}"}
            
            elif function_name == "get_market_context":
                try:
                    import yfinance as yf
                    
                    # Buscar dados do Ibovespa
                    ibov = yf.Ticker("^BVSP")
                    ibov_hist = ibov.history(period="5d")
                    
                    # Buscar dados do Dólar
                    usdbrl = yf.Ticker("BRL=X")
                    usd_hist = usdbrl.history(period="5d")
                    
                    ibov_current = float(ibov_hist['Close'].iloc[-1]) if len(ibov_hist) > 0 else None
                    ibov_prev = float(ibov_hist['Close'].iloc[-2]) if len(ibov_hist) > 1 else None
                    ibov_change = ((ibov_current - ibov_prev) / ibov_prev * 100) if ibov_current and ibov_prev else None
                    
                    usd_current = float(usd_hist['Close'].iloc[-1]) if len(usd_hist) > 0 else None
                    usd_prev = float(usd_hist['Close'].iloc[-2]) if len(usd_hist) > 1 else None
                    usd_change = ((usd_current - usd_prev) / usd_prev * 100) if usd_current and usd_prev else None
                    
                    result = {
                        "ibovespa": {
                            "value": round(ibov_current, 2) if ibov_current else "N/A",
                            "change_percent": round(ibov_change, 2) if ibov_change else "N/A",
                            "trend": "alta" if ibov_change and ibov_change > 0 else "baixa" if ibov_change else "estável"
                        },
                        "usd_brl": {
                            "value": round(usd_current, 2) if usd_current else "N/A",
                            "change_percent": round(usd_change, 2) if usd_change else "N/A",
                            "trend": "alta" if usd_change and usd_change > 0 else "baixa" if usd_change else "estável"
                        },
                        "selic": {
                            "value": "13.75%",
                            "note": "Taxa Selic atual (verificar BCB para valor atualizado)"
                        },
                        "sentiment": "Mercado em análise. Considere fatores macroeconômicos e específicos de cada setor."
                    }
                    
                    return _serialize_dates(result)
                except Exception as e:
                    return {"error": f"Erro ao buscar contexto de mercado: {str(e)}"}
            
            else:
                return {"error": f"Unknown function: {function_name}"}
        
        except Exception as e:
            logger.error(f"Error executing function {function_name}: {e}")
            return {"error": str(e)}
    
    def start_chat(self, system_instruction: Optional[str] = None) -> None:
        """
        Inicia uma nova sessão de chat.
        
        Args:
            system_instruction: Instrução de sistema opcional
        """
        if system_instruction is None:
            system_instruction = """Você é um assistente especializado em análise de ações brasileiras.
            
Você tem acesso a um sistema de ranking quantitativo que avalia ações da B3 usando três fatores:
- Momentum (40%): Tendências de preço e força relativa
- Qualidade (30%): Fundamentos e consistência financeira  
- Valor (30%): Atratividade de valuation

Além disso, você pode:
- Buscar informações sobre empresas (setor, negócio, descrição)
- Obter contexto do mercado (Ibovespa, dólar, Selic)
- Fazer buscas na web sobre notícias, análises e opiniões de especialistas
- Buscar notícias específicas sobre empresas

Quando o usuário perguntar sobre investimentos:
1. Use as ferramentas disponíveis para buscar dados reais
2. Combine análise quantitativa (scores) com contexto qualitativo (setor, mercado)
3. Use web_search para buscar notícias recentes, análises de especialistas e contexto atual
4. Considere o contexto macroeconômico atual
5. Forneça análises claras e objetivas baseadas em dados reais
6. Explique os scores em linguagem simples
7. Cite as fontes quando usar informações da web
8. SEMPRE mencione que não é recomendação de investimento e que o usuário deve consultar um profissional

Seja conversacional, amigável, educativo e baseie suas respostas em dados reais."""
        
        self.chat_history = []
        self.system_instruction = system_instruction
    
    async def send_message(self, message: str) -> str:
        """
        Envia uma mensagem e processa a resposta.
        
        Args:
            message: Mensagem do usuário
            
        Returns:
            Resposta do assistente
        """
        if not hasattr(self, 'chat_history'):
            self.start_chat()
        
        try:
            # Adicionar mensagem do usuário ao histórico
            self.chat_history.append(types.Content(
                role="user",
                parts=[types.Part(text=message)]
            ))
            
            # Criar configuração com tools
            tools = self._create_tools()
            
            # Loop para processar function calls
            max_iterations = 5
            for iteration in range(max_iterations):
                # Gerar resposta
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=self.chat_history,
                    config=types.GenerateContentConfig(
                        system_instruction=self.system_instruction,
                        tools=tools,
                        temperature=0.7
                    )
                )
                
                # Adicionar resposta ao histórico
                self.chat_history.append(response.candidates[0].content)
                
                # Verificar se há function calls
                has_function_call = False
                function_responses = []
                
                for part in response.candidates[0].content.parts:
                    if part.function_call:
                        has_function_call = True
                        function_name = part.function_call.name
                        function_args = dict(part.function_call.args)
                        
                        logger.info(f"Function call: {function_name} with args: {function_args}")
                        
                        # Executar função
                        function_result = await self._execute_function(function_name, function_args)
                        
                        # Criar resposta da função
                        function_responses.append(types.Part(
                            function_response=types.FunctionResponse(
                                name=function_name,
                                response={"result": function_result}
                            )
                        ))
                
                # Se não houver function calls, retornar texto
                if not has_function_call:
                    # Extrair texto da resposta
                    text_parts = [part.text for part in response.candidates[0].content.parts if part.text]
                    return " ".join(text_parts) if text_parts else "Desculpe, não consegui gerar uma resposta."
                
                # Adicionar respostas das funções ao histórico
                if function_responses:
                    self.chat_history.append(types.Content(
                        role="user",
                        parts=function_responses
                    ))
            
            return "Desculpe, atingi o limite de iterações ao processar sua mensagem."
        
        except Exception as e:
            logger.error(f"Error in send_message: {e}", exc_info=True)
            return f"Desculpe, ocorreu um erro ao processar sua mensagem: {str(e)}"
    
    def get_history(self) -> List[Dict[str, str]]:
        """
        Obtém o histórico da conversa.
        
        Returns:
            Lista de mensagens com role e content
        """
        if not hasattr(self, 'chat_history'):
            return []
        
        history = []
        for content in self.chat_history:
            role = "user" if content.role == "user" else "assistant"
            # Extrair texto das parts
            text_parts = [part.text for part in content.parts if hasattr(part, 'text') and part.text]
            if text_parts:
                history.append({"role": role, "content": " ".join(text_parts)})
        
        return history
