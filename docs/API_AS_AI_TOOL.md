# API como Tool para Soluções de IA

Guia completo para integrar a API do Quant Stock Ranker como ferramenta (tool/function) em sistemas de IA.

## 📋 Visão Geral

A API fornece endpoints REST para:
- Obter ranking atual de ações
- Consultar ranking histórico
- Buscar informações de ativos específicos
- Executar pipeline de atualização

## 🔗 Endpoints Disponíveis

### Base URL
```
http://localhost:8000
```

### Endpoints Principais

| Endpoint | Método | Descrição |
|----------|--------|-----------|
| `/api/ranking/latest` | GET | Ranking mais recente |
| `/api/ranking/date/{date}` | GET | Ranking de data específica |
| `/api/asset/{ticker}/history` | GET | Histórico de um ativo |
| `/api/pipeline/run` | POST | Executar pipeline |
| `/health` | GET | Status da API |

## 🤖 Integração com OpenAI Function Calling

### 1. Definição das Functions

```python
import requests
from typing import Optional, List, Dict
import json

# Definição das tools para OpenAI
tools = [
    {
        "type": "function",
        "function": {
            "name": "get_stock_ranking",
            "description": "Obtém o ranking quantitativo atual das melhores ações da B3 baseado em fatores de momentum, value, quality e risk. Retorna top 10 ações com scores e métricas.",
            "parameters": {
                "type": "object",
                "properties": {
                    "top_n": {
                        "type": "integer",
                        "description": "Número de ações a retornar (padrão: 10)",
                        "default": 10
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_stock_ranking_by_date",
            "description": "Obtém o ranking quantitativo de ações em uma data específica. Útil para análise histórica.",
            "parameters": {
                "type": "object",
                "properties": {
                    "date": {
                        "type": "string",
                        "description": "Data no formato YYYY-MM-DD (ex: 2024-03-01)",
                    }
                },
                "required": ["date"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_stock_details",
            "description": "Obtém detalhes e histórico de performance de uma ação específica, incluindo scores de momentum, value, quality e evolução temporal.",
            "parameters": {
                "type": "object",
                "properties": {
                    "ticker": {
                        "type": "string",
                        "description": "Código da ação (ex: ITUB3, PETR4, VALE3)",
                    }
                },
                "required": ["ticker"]
            }
        }
    }
]

# Implementação das funções
def get_stock_ranking(top_n: int = 10) -> Dict:
    """Obtém ranking atual de ações"""
    try:
        response = requests.get(
            "http://localhost:8000/api/ranking/latest",
            params={"top_n": top_n},
            timeout=10
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {"error": str(e)}

def get_stock_ranking_by_date(date: str) -> Dict:
    """Obtém ranking de data específica"""
    try:
        response = requests.get(
            f"http://localhost:8000/api/ranking/date/{date}",
            timeout=10
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {"error": str(e)}

def get_stock_details(ticker: str) -> Dict:
    """Obtém detalhes de uma ação"""
    try:
        response = requests.get(
            f"http://localhost:8000/api/asset/{ticker}/history",
            timeout=10
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {"error": str(e)}

# Mapeamento de funções
available_functions = {
    "get_stock_ranking": get_stock_ranking,
    "get_stock_ranking_by_date": get_stock_ranking_by_date,
    "get_stock_details": get_stock_details,
}
```

### 2. Uso com OpenAI

```python
from openai import OpenAI

client = OpenAI(api_key="sua-api-key")

def chat_with_stock_advisor(user_message: str):
    """Chat com assistente de investimentos"""
    
    messages = [
        {
            "role": "system",
            "content": """Você é um assistente especializado em análise quantitativa de ações da B3.
            Use as ferramentas disponíveis para fornecer recomendações baseadas em dados.
            Explique os scores de forma clara: momentum (tendência), value (valor), quality (qualidade), risk (risco)."""
        },
        {
            "role": "user",
            "content": user_message
        }
    ]
    
    # Primeira chamada
    response = client.chat.completions.create(
        model="gpt-4-turbo-preview",
        messages=messages,
        tools=tools,
        tool_choice="auto"
    )
    
    response_message = response.choices[0].message
    tool_calls = response_message.tool_calls
    
    # Se a IA quer usar uma tool
    if tool_calls:
        messages.append(response_message)
        
        # Executar cada tool call
        for tool_call in tool_calls:
            function_name = tool_call.function.name
            function_args = json.loads(tool_call.function.arguments)
            
            # Executar função
            function_to_call = available_functions[function_name]
            function_response = function_to_call(**function_args)
            
            # Adicionar resposta da função
            messages.append({
                "tool_call_id": tool_call.id,
                "role": "tool",
                "name": function_name,
                "content": json.dumps(function_response)
            })
        
        # Segunda chamada com resultados das tools
        second_response = client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=messages
        )
        
        return second_response.choices[0].message.content
    
    return response_message.content

# Exemplo de uso
if __name__ == "__main__":
    # Pergunta do usuário
    resposta = chat_with_stock_advisor(
        "Quais são as melhores ações para investir agora? Me dê o top 5 com justificativa."
    )
    print(resposta)
```

## 🔷 Integração com Anthropic Claude

```python
import anthropic
import json

client = anthropic.Anthropic(api_key="sua-api-key")

# Definição das tools para Claude
tools_claude = [
    {
        "name": "get_stock_ranking",
        "description": "Obtém o ranking quantitativo atual das melhores ações da B3 baseado em fatores de momentum, value, quality e risk",
        "input_schema": {
            "type": "object",
            "properties": {
                "top_n": {
                    "type": "number",
                    "description": "Número de ações a retornar (padrão: 10)"
                }
            }
        }
    },
    {
        "name": "get_stock_details",
        "description": "Obtém detalhes e histórico de uma ação específica",
        "input_schema": {
            "type": "object",
            "properties": {
                "ticker": {
                    "type": "string",
                    "description": "Código da ação (ex: ITUB3, PETR4)"
                }
            },
            "required": ["ticker"]
        }
    }
]

def chat_with_claude(user_message: str):
    """Chat com Claude usando tools"""
    
    messages = [{"role": "user", "content": user_message}]
    
    response = client.messages.create(
        model="claude-3-opus-20240229",
        max_tokens=4096,
        tools=tools_claude,
        messages=messages
    )
    
    # Processar tool uses
    while response.stop_reason == "tool_use":
        tool_use = next(block for block in response.content if block.type == "tool_use")
        
        # Executar função
        function_name = tool_use.name
        function_args = tool_use.input
        function_to_call = available_functions[function_name]
        function_response = function_to_call(**function_args)
        
        # Adicionar resultado
        messages.append({"role": "assistant", "content": response.content})
        messages.append({
            "role": "user",
            "content": [{
                "type": "tool_result",
                "tool_use_id": tool_use.id,
                "content": json.dumps(function_response)
            }]
        })
        
        # Nova chamada
        response = client.messages.create(
            model="claude-3-opus-20240229",
            max_tokens=4096,
            tools=tools_claude,
            messages=messages
        )
    
    return response.content[0].text
```

## 🦜 Integração com LangChain

```python
from langchain.tools import Tool
from langchain.agents import initialize_agent, AgentType
from langchain.chat_models import ChatOpenAI

# Criar tools do LangChain
langchain_tools = [
    Tool(
        name="get_stock_ranking",
        func=lambda top_n=10: get_stock_ranking(int(top_n)),
        description="Obtém ranking atual das melhores ações da B3. Input: número de ações (padrão 10)"
    ),
    Tool(
        name="get_stock_details",
        func=get_stock_details,
        description="Obtém detalhes de uma ação específica. Input: ticker da ação (ex: ITUB3)"
    ),
    Tool(
        name="get_stock_ranking_by_date",
        func=get_stock_ranking_by_date,
        description="Obtém ranking de data específica. Input: data no formato YYYY-MM-DD"
    )
]

# Criar agente
llm = ChatOpenAI(model="gpt-4-turbo-preview", temperature=0)

agent = initialize_agent(
    tools=langchain_tools,
    llm=llm,
    agent=AgentType.OPENAI_FUNCTIONS,
    verbose=True
)

# Usar agente
response = agent.run(
    "Quais são as top 5 ações agora e me dê detalhes sobre ITUB3"
)
print(response)
```

## 🔧 Integração com LlamaIndex

```python
from llama_index.tools import FunctionTool
from llama_index.agent import OpenAIAgent

# Criar tools do LlamaIndex
tools_llama = [
    FunctionTool.from_defaults(
        fn=get_stock_ranking,
        name="get_stock_ranking",
        description="Obtém ranking atual das melhores ações da B3"
    ),
    FunctionTool.from_defaults(
        fn=get_stock_details,
        name="get_stock_details",
        description="Obtém detalhes de uma ação específica"
    )
]

# Criar agente
agent = OpenAIAgent.from_tools(
    tools_llama,
    verbose=True
)

# Usar agente
response = agent.chat("Quais são as melhores ações para investir?")
print(response)
```

## 📱 Exemplo Completo: Chatbot de Investimentos

```python
import requests
import json
from openai import OpenAI
from typing import Dict, List

class StockAdvisorBot:
    """Chatbot de assessoria de investimentos usando API Quant"""
    
    def __init__(self, api_base_url: str = "http://localhost:8000"):
        self.api_base_url = api_base_url
        self.client = OpenAI()
        self.conversation_history = []
        
    def get_stock_ranking(self, top_n: int = 10) -> Dict:
        """Obtém ranking atual"""
        response = requests.get(
            f"{self.api_base_url}/api/ranking/latest",
            params={"top_n": top_n}
        )
        return response.json()
    
    def get_stock_details(self, ticker: str) -> Dict:
        """Obtém detalhes de ação"""
        response = requests.get(
            f"{self.api_base_url}/api/asset/{ticker}/history"
        )
        return response.json()
    
    def chat(self, user_message: str) -> str:
        """Processa mensagem do usuário"""
        
        # Adicionar mensagem do usuário
        self.conversation_history.append({
            "role": "user",
            "content": user_message
        })
        
        # Definir tools
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "get_stock_ranking",
                    "description": "Obtém ranking quantitativo das melhores ações da B3",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "top_n": {"type": "integer", "default": 10}
                        }
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_stock_details",
                    "description": "Obtém detalhes de uma ação específica",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "ticker": {"type": "string"}
                        },
                        "required": ["ticker"]
                    }
                }
            }
        ]
        
        # Chamar OpenAI
        response = self.client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[
                {
                    "role": "system",
                    "content": """Você é um assistente especializado em investimentos na B3.
                    Use análise quantitativa baseada em momentum, value, quality e risk.
                    Seja claro e objetivo nas recomendações."""
                }
            ] + self.conversation_history,
            tools=tools,
            tool_choice="auto"
        )
        
        response_message = response.choices[0].message
        
        # Processar tool calls
        if response_message.tool_calls:
            self.conversation_history.append(response_message)
            
            for tool_call in response_message.tool_calls:
                function_name = tool_call.function.name
                function_args = json.loads(tool_call.function.arguments)
                
                # Executar função
                if function_name == "get_stock_ranking":
                    result = self.get_stock_ranking(**function_args)
                elif function_name == "get_stock_details":
                    result = self.get_stock_details(**function_args)
                
                # Adicionar resultado
                self.conversation_history.append({
                    "tool_call_id": tool_call.id,
                    "role": "tool",
                    "name": function_name,
                    "content": json.dumps(result)
                })
            
            # Segunda chamada
            second_response = self.client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[
                    {
                        "role": "system",
                        "content": """Você é um assistente especializado em investimentos na B3."""
                    }
                ] + self.conversation_history
            )
            
            assistant_message = second_response.choices[0].message.content
        else:
            assistant_message = response_message.content
        
        # Adicionar resposta do assistente
        self.conversation_history.append({
            "role": "assistant",
            "content": assistant_message
        })
        
        return assistant_message

# Exemplo de uso
if __name__ == "__main__":
    bot = StockAdvisorBot()
    
    print("🤖 Chatbot de Investimentos - Quant Stock Ranker")
    print("Digite 'sair' para encerrar\n")
    
    while True:
        user_input = input("Você: ")
        if user_input.lower() in ['sair', 'exit', 'quit']:
            break
        
        response = bot.chat(user_input)
        print(f"\n🤖 Assistente: {response}\n")
```

## 🌐 Exemplo com FastAPI (Webhook)

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import requests

app = FastAPI()

class ChatRequest(BaseModel):
    message: str
    user_id: str

@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    """Endpoint para chat com IA"""
    
    bot = StockAdvisorBot()
    response = bot.chat(request.message)
    
    return {
        "user_id": request.user_id,
        "response": response
    }

@app.get("/ranking")
async def get_ranking(top_n: int = 10):
    """Endpoint proxy para ranking"""
    try:
        response = requests.get(
            "http://localhost:8000/api/ranking/latest",
            params={"top_n": top_n}
        )
        return response.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

## 📊 Formato de Resposta da API

### Ranking Latest
```json
{
  "date": "2024-03-07",
  "ranking": [
    {
      "rank": 1,
      "ticker": "ITUB3",
      "final_score": 0.85,
      "momentum_score": 0.90,
      "value_score": 0.75,
      "quality_score": 0.88,
      "confidence": 0.92
    }
  ],
  "total_assets": 50
}
```

### Asset History
```json
{
  "ticker": "ITUB3",
  "history": [
    {
      "date": "2024-03-01",
      "final_score": 0.85,
      "rank": 1
    }
  ],
  "statistics": {
    "avg_score": 0.82,
    "avg_rank": 2.5
  }
}
```

## 🔐 Segurança

### Autenticação (se implementada)
```python
headers = {
    "Authorization": "Bearer YOUR_API_KEY"
}

response = requests.get(
    "http://localhost:8000/api/ranking/latest",
    headers=headers
)
```

### Rate Limiting
```python
import time
from functools import wraps

def rate_limit(max_calls: int, period: int):
    """Decorator para rate limiting"""
    calls = []
    
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            now = time.time()
            calls_in_period = [c for c in calls if c > now - period]
            
            if len(calls_in_period) >= max_calls:
                sleep_time = period - (now - calls_in_period[0])
                time.sleep(sleep_time)
            
            calls.append(time.time())
            return func(*args, **kwargs)
        return wrapper
    return decorator

@rate_limit(max_calls=10, period=60)
def get_stock_ranking_limited(top_n: int = 10):
    return get_stock_ranking(top_n)
```

## 📚 Recursos Adicionais

- **Documentação API**: http://localhost:8000/docs
- **OpenAPI Schema**: http://localhost:8000/openapi.json
- **Health Check**: http://localhost:8000/health

---

**Versão**: 2.7.0  
**Data**: Março 2026  
**Status**: ✅ Pronto para Integração
