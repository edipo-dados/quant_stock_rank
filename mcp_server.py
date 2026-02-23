"""
MCP Server para Quant Stock Ranker

Expõe funcionalidades do sistema de ranking quantitativo de ações
para agentes conversacionais via Model Context Protocol (MCP).
"""

import asyncio
import json
from typing import Any, Optional
import httpx
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

# Configuração da API
API_BASE_URL = "http://localhost:8000"

# Criar servidor MCP
app = Server("quant-stock-ranker")


@app.list_tools()
async def list_tools() -> list[Tool]:
    """Lista todas as ferramentas disponíveis."""
    return [
        Tool(
            name="get_ranking",
            description="Obtém o ranking completo de ações ordenado por score. Retorna lista de ativos com scores de momentum, qualidade e valor.",
            inputSchema={
                "type": "object",
                "properties": {
                    "date": {
                        "type": "string",
                        "description": "Data do ranking no formato YYYY-MM-DD (opcional, usa data mais recente se não fornecido)",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Número máximo de ativos a retornar (opcional, padrão: todos)",
                        "minimum": 1,
                        "maximum": 200,
                    }
                },
            },
        ),
        Tool(
            name="get_top_stocks",
            description="Obtém os top N ativos com maior score final. Útil para identificar as melhores oportunidades de investimento.",
            inputSchema={
                "type": "object",
                "properties": {
                    "n": {
                        "type": "integer",
                        "description": "Número de ativos a retornar (padrão: 10)",
                        "minimum": 1,
                        "maximum": 100,
                        "default": 10,
                    },
                    "date": {
                        "type": "string",
                        "description": "Data do ranking no formato YYYY-MM-DD (opcional)",
                    }
                },
                "required": [],
            },
        ),
        Tool(
            name="get_asset_details",
            description="Obtém detalhes completos de um ativo específico incluindo score, breakdown por fator, posição no ranking, explicação automática e fatores normalizados.",
            inputSchema={
                "type": "object",
                "properties": {
                    "ticker": {
                        "type": "string",
                        "description": "Símbolo do ativo (ex: PETR4.SA, VALE3.SA, ITUB4.SA)",
                    },
                    "date": {
                        "type": "string",
                        "description": "Data do score no formato YYYY-MM-DD (opcional)",
                    }
                },
                "required": ["ticker"],
            },
        ),
        Tool(
            name="get_price_history",
            description="Obtém histórico de preços diários de um ativo. Retorna dados de open, high, low, close, volume e adj_close.",
            inputSchema={
                "type": "object",
                "properties": {
                    "ticker": {
                        "type": "string",
                        "description": "Símbolo do ativo (ex: PETR4.SA, VALE3.SA)",
                    },
                    "days": {
                        "type": "integer",
                        "description": "Número de dias de histórico (padrão: 365, máximo: 3650)",
                        "minimum": 1,
                        "maximum": 3650,
                        "default": 365,
                    }
                },
                "required": ["ticker"],
            },
        ),
        Tool(
            name="compare_assets",
            description="Compara múltiplos ativos lado a lado mostrando seus scores e posições no ranking. Útil para análise comparativa.",
            inputSchema={
                "type": "object",
                "properties": {
                    "tickers": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Lista de tickers para comparar (ex: ['PETR4.SA', 'VALE3.SA', 'ITUB4.SA'])",
                        "minItems": 2,
                        "maxItems": 10,
                    },
                    "date": {
                        "type": "string",
                        "description": "Data para comparação no formato YYYY-MM-DD (opcional)",
                    }
                },
                "required": ["tickers"],
            },
        ),
        Tool(
            name="search_by_criteria",
            description="Busca ativos que atendem critérios específicos de score. Útil para filtrar ações por momentum, qualidade ou valor.",
            inputSchema={
                "type": "object",
                "properties": {
                    "min_momentum": {
                        "type": "number",
                        "description": "Score mínimo de momentum (-1 a 1)",
                    },
                    "min_quality": {
                        "type": "number",
                        "description": "Score mínimo de qualidade (-1 a 1)",
                    },
                    "min_value": {
                        "type": "number",
                        "description": "Score mínimo de valor (-1 a 1)",
                    },
                    "min_final_score": {
                        "type": "number",
                        "description": "Score final mínimo (-1 a 1)",
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Número máximo de resultados (padrão: 20)",
                        "default": 20,
                    }
                },
                "required": [],
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: Any) -> list[TextContent]:
    """Executa uma ferramenta."""
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            if name == "get_ranking":
                # Obter ranking completo
                params = {}
                if "date" in arguments:
                    params["date"] = arguments["date"]
                
                response = await client.get(f"{API_BASE_URL}/api/v1/ranking", params=params)
                response.raise_for_status()
                data = response.json()
                
                # Aplicar limite se fornecido
                if "limit" in arguments:
                    data["rankings"] = data["rankings"][:arguments["limit"]]
                    data["total_assets"] = len(data["rankings"])
                
                return [TextContent(
                    type="text",
                    text=json.dumps(data, indent=2, ensure_ascii=False)
                )]
            
            elif name == "get_top_stocks":
                # Obter top N ativos
                n = arguments.get("n", 10)
                params = {"n": n}
                if "date" in arguments:
                    params["date"] = arguments["date"]
                
                response = await client.get(f"{API_BASE_URL}/api/v1/top", params=params)
                response.raise_for_status()
                data = response.json()
                
                return [TextContent(
                    type="text",
                    text=json.dumps(data, indent=2, ensure_ascii=False)
                )]
            
            elif name == "get_asset_details":
                # Obter detalhes de um ativo
                ticker = arguments["ticker"].upper()
                params = {}
                if "date" in arguments:
                    params["date"] = arguments["date"]
                
                response = await client.get(
                    f"{API_BASE_URL}/api/v1/asset/{ticker}",
                    params=params
                )
                response.raise_for_status()
                data = response.json()
                
                return [TextContent(
                    type="text",
                    text=json.dumps(data, indent=2, ensure_ascii=False)
                )]
            
            elif name == "get_price_history":
                # Obter histórico de preços
                ticker = arguments["ticker"].upper()
                days = arguments.get("days", 365)
                
                response = await client.get(
                    f"{API_BASE_URL}/api/v1/prices/{ticker}",
                    params={"days": days}
                )
                response.raise_for_status()
                data = response.json()
                
                return [TextContent(
                    type="text",
                    text=json.dumps(data, indent=2, ensure_ascii=False)
                )]
            
            elif name == "compare_assets":
                # Comparar múltiplos ativos
                tickers = [t.upper() for t in arguments["tickers"]]
                date_param = arguments.get("date")
                
                # Buscar detalhes de cada ticker
                comparisons = []
                for ticker in tickers:
                    params = {}
                    if date_param:
                        params["date"] = date_param
                    
                    try:
                        response = await client.get(
                            f"{API_BASE_URL}/api/v1/asset/{ticker}",
                            params=params
                        )
                        response.raise_for_status()
                        asset_data = response.json()
                        
                        # Extrair informações relevantes para comparação
                        comparisons.append({
                            "ticker": ticker,
                            "final_score": asset_data["score"]["final_score"],
                            "rank": asset_data["score"]["rank"],
                            "momentum_score": asset_data["score"]["momentum_score"],
                            "quality_score": asset_data["score"]["quality_score"],
                            "value_score": asset_data["score"]["value_score"],
                            "confidence": asset_data["score"]["confidence"],
                        })
                    except httpx.HTTPError as e:
                        comparisons.append({
                            "ticker": ticker,
                            "error": str(e)
                        })
                
                result = {
                    "date": date_param or "latest",
                    "comparison": comparisons
                }
                
                return [TextContent(
                    type="text",
                    text=json.dumps(result, indent=2, ensure_ascii=False)
                )]
            
            elif name == "search_by_criteria":
                # Buscar por critérios
                params = {}
                if "date" in arguments:
                    params["date"] = arguments["date"]
                
                # Obter ranking completo
                response = await client.get(f"{API_BASE_URL}/api/v1/ranking", params=params)
                response.raise_for_status()
                data = response.json()
                
                # Filtrar por critérios
                filtered = []
                for asset in data["rankings"]:
                    if "min_momentum" in arguments and asset["momentum_score"] < arguments["min_momentum"]:
                        continue
                    if "min_quality" in arguments and asset["quality_score"] < arguments["min_quality"]:
                        continue
                    if "min_value" in arguments and asset["value_score"] < arguments["min_value"]:
                        continue
                    if "min_final_score" in arguments and asset["final_score"] < arguments["min_final_score"]:
                        continue
                    
                    filtered.append(asset)
                
                # Aplicar limite
                max_results = arguments.get("max_results", 20)
                filtered = filtered[:max_results]
                
                result = {
                    "criteria": {k: v for k, v in arguments.items() if k.startswith("min_")},
                    "total_found": len(filtered),
                    "results": filtered
                }
                
                return [TextContent(
                    type="text",
                    text=json.dumps(result, indent=2, ensure_ascii=False)
                )]
            
            else:
                return [TextContent(
                    type="text",
                    text=json.dumps({"error": f"Unknown tool: {name}"})
                )]
        
        except httpx.HTTPError as e:
            return [TextContent(
                type="text",
                text=json.dumps({
                    "error": str(e),
                    "details": "Verifique se a API está rodando em http://localhost:8000"
                })
            )]
        except Exception as e:
            return [TextContent(
                type="text",
                text=json.dumps({"error": str(e)})
            )]


async def main():
    """Inicia o servidor MCP."""
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())
