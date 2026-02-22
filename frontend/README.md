# Frontend Streamlit - Sistema de Ranking Quantitativo

Interface web para visualização de rankings e análise de ativos.

## Estrutura

```
frontend/
├── streamlit_app.py          # Aplicação principal
├── pages/
│   ├── 1_🏆_Ranking.py       # Página de ranking completo
│   └── 2_📊_Detalhes_do_Ativo.py  # Página de detalhes do ativo
└── README.md
```

## Funcionalidades

### Página de Ranking (🏆)
- Visualização de ranking completo de todos os ativos
- Tabela ordenável com score, confiança e posição
- Busca por ticker
- Estatísticas do ranking (média, máximo, mínimo, desvio padrão)
- Navegação para detalhes do ativo

### Página de Detalhes do Ativo (📊)
- Score final e posição no ranking
- Breakdown de scores por categoria (Momentum, Qualidade, Valor)
- Análise automática em português
- Fatores normalizados detalhados
- Gráfico de preços dos últimos 12 meses
- Estatísticas de preço (atual, variação 12M, máxima, mínima)

## Como Executar

### Pré-requisitos

1. Backend da API deve estar rodando (porta 8000 por padrão)
2. Dependências instaladas:
   ```bash
   pip install -r requirements.txt
   ```

### Executar Localmente

```bash
# A partir do diretório raiz do projeto
streamlit run frontend/streamlit_app.py
```

O frontend estará disponível em: http://localhost:8501

### Configuração

A URL do backend pode ser configurada no arquivo `.env`:

```env
BACKEND_URL=http://localhost:8000
```

Padrão: `http://localhost:8000`

## Navegação

1. **Página Principal**: Instruções e visão geral do sistema
2. **Ranking**: Visualize o ranking completo de ativos
3. **Detalhes do Ativo**: Análise detalhada de um ativo específico

### Fluxo de Uso

1. Acesse a página de Ranking
2. Visualize a tabela com todos os ativos rankeados
3. Clique em "Ver Detalhes" para um ativo específico
4. Ou digite um ticker na página de Detalhes do Ativo

## Dependências

- **streamlit**: Framework web para Python
- **requests**: Cliente HTTP para consumir a API
- **pandas**: Manipulação de dados
- **plotly**: Gráficos interativos
- **yfinance**: Dados históricos de preços

## Validação

Este frontend valida os seguintes requisitos:

- **11.1**: Exibir tabela ordenável com todos os ativos
- **11.2**: Mostrar score, confiança e posição no ranking
- **11.3**: Navegar para página de detalhes
- **11.4**: Exibir score total
- **11.5**: Mostrar breakdown de fatores por categoria
- **11.6**: Mostrar texto de explicação automatizada
- **11.7**: Mostrar gráfico de preço de 12 meses
- **11.8**: Consumir dados dos endpoints REST da API

## Testes

Os testes de propriedade para consumo da API estão em:
```
tests/unit/test_frontend_api_consumption.py
```

Execute com:
```bash
pytest tests/unit/test_frontend_api_consumption.py -v
```

## Notas

- O frontend consome dados da API REST em tempo real
- Não há cache de dados - todas as requisições vão para a API
- O histórico de preços é buscado diretamente do Yahoo Finance via yfinance
- A interface é responsiva e otimizada para desktop
