# MCP Server - Quant Stock Ranker

Servidor MCP (Model Context Protocol) que expõe as funcionalidades do sistema de ranking quantitativo de ações para agentes conversacionais.

## O que é MCP?

MCP (Model Context Protocol) é um protocolo que permite que agentes de IA (como Claude, ChatGPT, etc.) acessem ferramentas e dados externos de forma padronizada. Com este servidor MCP, você pode conversar com um agente sobre ações brasileiras e ele terá acesso direto aos dados de ranking.

## Instalação

### 1. Instalar dependências MCP

```bash
pip install mcp httpx
```

Ou adicione ao `requirements.txt`:
```
mcp>=0.9.0
httpx>=0.27.0
```

### 2. Garantir que a API está rodando

O MCP server precisa que a API FastAPI esteja rodando:

```bash
# Iniciar containers Docker
docker-compose up -d

# Verificar se API está respondendo
curl http://localhost:8000/health
```

## Uso

### Iniciar o MCP Server

```bash
# Diretamente
python mcp_server.py

# Ou via uvx (recomendado para produção)
uvx mcp_server.py
```

### Configurar em um Cliente MCP

#### Claude Desktop

Adicione ao arquivo de configuração do Claude Desktop (`claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "quant-stock-ranker": {
      "command": "python",
      "args": ["C:/caminho/para/quant_stock_rank/mcp_server.py"],
      "env": {
        "PYTHONPATH": "C:/caminho/para/quant_stock_rank"
      }
    }
  }
}
```

#### Cline (VS Code)

Adicione ao arquivo `.vscode/mcp.json`:

```json
{
  "mcpServers": {
    "quant-stock-ranker": {
      "command": "python",
      "args": ["mcp_server.py"],
      "cwd": "${workspaceFolder}/quant_stock_rank"
    }
  }
}
```

## Ferramentas Disponíveis

### 1. get_ranking

Obtém o ranking completo de ações ordenado por score.

**Parâmetros:**
- `date` (opcional): Data no formato YYYY-MM-DD
- `limit` (opcional): Número máximo de ativos (1-200)

**Exemplo de uso no chat:**
```
"Mostre o ranking completo de ações"
"Quais são as top 20 ações hoje?"
"Me mostre o ranking do dia 2026-02-20"
```

### 2. get_top_stocks

Obtém os top N ativos com maior score.

**Parâmetros:**
- `n` (opcional): Número de ativos (padrão: 10, máximo: 100)
- `date` (opcional): Data no formato YYYY-MM-DD

**Exemplo de uso no chat:**
```
"Quais são as 5 melhores ações para investir?"
"Me mostre as top 10 ações"
"Quais eram as 3 melhores ações em 2026-02-15?"
```

### 3. get_asset_details

Obtém detalhes completos de um ativo específico.

**Parâmetros:**
- `ticker` (obrigatório): Símbolo do ativo (ex: PETR4.SA)
- `date` (opcional): Data no formato YYYY-MM-DD

**Exemplo de uso no chat:**
```
"Me fale sobre PETR4.SA"
"Quais são os detalhes de VALE3.SA?"
"Como está o score de ITUB4.SA?"
"Analise BBDC4.SA para mim"
```

### 4. get_price_history

Obtém histórico de preços diários de um ativo.

**Parâmetros:**
- `ticker` (obrigatório): Símbolo do ativo
- `days` (opcional): Número de dias (padrão: 365, máximo: 3650)

**Exemplo de uso no chat:**
```
"Mostre o histórico de preços de PETR4.SA"
"Quais foram os preços de VALE3.SA nos últimos 30 dias?"
"Me mostre 1 ano de preços de ITUB4.SA"
```

### 5. compare_assets

Compara múltiplos ativos lado a lado.

**Parâmetros:**
- `tickers` (obrigatório): Lista de 2-10 tickers
- `date` (opcional): Data para comparação

**Exemplo de uso no chat:**
```
"Compare PETR4.SA com VALE3.SA"
"Qual é melhor: ITUB4.SA, BBDC4.SA ou BBAS3.SA?"
"Compare as 3 maiores petroleiras"
```

### 6. search_by_criteria

Busca ativos que atendem critérios específicos.

**Parâmetros:**
- `min_momentum` (opcional): Score mínimo de momentum
- `min_quality` (opcional): Score mínimo de qualidade
- `min_value` (opcional): Score mínimo de valor
- `min_final_score` (opcional): Score final mínimo
- `max_results` (opcional): Número máximo de resultados (padrão: 20)

**Exemplo de uso no chat:**
```
"Quais ações têm momentum acima de 0.5?"
"Me mostre ações com qualidade alta (>0.6)"
"Busque ações baratas com valor acima de 0.4"
"Quais ações têm score final acima de 0.3?"
```

## Exemplos de Conversas

### Exemplo 1: Análise Básica

```
Usuário: Quais são as 5 melhores ações para investir hoje?
Agente: [usa get_top_stocks com n=5]
Agente: As 5 melhores ações hoje são:
1. CYRE3.SA - Score: 0.333
2. PRIO3.SA - Score: 0.321
3. GGBR4.SA - Score: 0.298
...
```

### Exemplo 2: Análise Detalhada

```
Usuário: Me fale sobre PETR4.SA
Agente: [usa get_asset_details com ticker=PETR4.SA]
Agente: PETR4.SA está na posição #12 do ranking com score 0.245.

Breakdown:
- Momentum: 0.42 (forte tendência de alta)
- Qualidade: 0.31 (fundamentos sólidos)
- Valor: -0.08 (um pouco cara)

Pontos fortes:
- Retorno de 12 meses acima da média
- ROE consistente
...
```

### Exemplo 3: Comparação

```
Usuário: Compare PETR4.SA com VALE3.SA
Agente: [usa compare_assets com tickers=['PETR4.SA', 'VALE3.SA']]
Agente: Comparação entre PETR4.SA e VALE3.SA:

PETR4.SA:
- Posição: #12
- Score Final: 0.245
- Momentum: 0.42 (melhor)
- Qualidade: 0.31
- Valor: -0.08

VALE3.SA:
- Posição: #8
- Score Final: 0.267
- Momentum: 0.38
- Qualidade: 0.45 (melhor)
- Valor: 0.02 (melhor)

Conclusão: VALE3.SA tem score geral melhor...
```

### Exemplo 4: Busca por Critérios

```
Usuário: Quais ações têm momentum forte e qualidade boa?
Agente: [usa search_by_criteria com min_momentum=0.5, min_quality=0.4]
Agente: Encontrei 8 ações com momentum >0.5 e qualidade >0.4:

1. GGBR4.SA - M: 0.67, Q: 0.52
2. PRIO3.SA - M: 0.58, Q: 0.48
3. CYRE3.SA - M: 0.55, Q: 0.45
...
```

## Configuração Avançada

### Alterar URL da API

Se sua API está em outra porta ou host, edite `mcp_server.py`:

```python
API_BASE_URL = "http://localhost:8000"  # Altere aqui
```

### Timeout

Para ajustar o timeout das requisições:

```python
async with httpx.AsyncClient(timeout=30.0) as client:  # Altere aqui
```

### Adicionar Autenticação

Se sua API requer autenticação, adicione headers:

```python
headers = {"Authorization": "Bearer seu-token"}
response = await client.get(url, headers=headers)
```

## Troubleshooting

### Erro: "Connection refused"

**Causa**: API não está rodando.

**Solução**:
```bash
docker-compose up -d
curl http://localhost:8000/health
```

### Erro: "Tool not found"

**Causa**: Cliente MCP não reconhece as ferramentas.

**Solução**: Reinicie o cliente MCP (Claude Desktop, Cline, etc.)

### Erro: "Timeout"

**Causa**: Requisição demorou muito.

**Solução**: Aumente o timeout em `mcp_server.py`:
```python
async with httpx.AsyncClient(timeout=60.0) as client:
```

### MCP Server não inicia

**Causa**: Dependências não instaladas.

**Solução**:
```bash
pip install mcp httpx
```

## Desenvolvimento

### Adicionar Nova Ferramenta

1. Adicione a ferramenta em `list_tools()`:

```python
Tool(
    name="minha_ferramenta",
    description="Descrição da ferramenta",
    inputSchema={
        "type": "object",
        "properties": {
            "param1": {
                "type": "string",
                "description": "Descrição do parâmetro"
            }
        },
        "required": ["param1"]
    }
)
```

2. Implemente em `call_tool()`:

```python
elif name == "minha_ferramenta":
    # Implementação
    result = {"data": "..."}
    return [TextContent(type="text", text=json.dumps(result))]
```

### Testar Localmente

```bash
# Iniciar servidor
python mcp_server.py

# Em outro terminal, testar com curl
echo '{"method":"tools/list"}' | python mcp_server.py
```

## Segurança

- O MCP server acessa apenas a API local (localhost:8000)
- Não expõe dados sensíveis além do que a API já expõe
- Não requer autenticação (mesma política da API)
- Recomendado usar apenas em ambiente local/desenvolvimento

Para produção:
- Adicione autenticação na API
- Use HTTPS
- Limite acesso por IP
- Implemente rate limiting

## Referências

- [MCP Documentation](https://modelcontextprotocol.io/)
- [Claude Desktop MCP](https://docs.anthropic.com/claude/docs/mcp)
- [API Documentation](http://localhost:8000/docs)
- [Guia de Uso](docs/GUIA_USO.md)
