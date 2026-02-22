# Plano de Implementação: Sistema de Ranking Quantitativo de Ações

## Visão Geral

Este plano detalha a implementação do sistema de ranking quantitativo de ações em Python 3.11+, seguindo a arquitetura modular definida no documento de design. A implementação será incremental, com validação contínua através de testes.

## Tarefas

- [x] 1. Configurar estrutura do projeto e dependências
  - Criar estrutura de diretórios conforme design
  - Criar requirements.txt com dependências (FastAPI, SQLAlchemy, pandas, yfinance, requests, hypothesis, pytest, streamlit)
  - Criar arquivo .env.example com variáveis de ambiente
  - Criar arquivo config.py para gerenciamento de configurações
  - _Requisitos: 9.1, 9.3, 9.4, 9.5, 13.1, 13.2, 13.3_

- [x] 2. Implementar modelos de banco de dados e inicialização
  - [x] 2.1 Criar modelos SQLAlchemy para todas as tabelas
    - Implementar RawPriceDaily com índices e constraints
    - Implementar RawFundamental com índices e constraints
    - Implementar FeatureDaily com índices e constraints
    - Implementar FeatureMonthly com índices e constraints
    - Implementar ScoreDaily com índices e constraints
    - _Requisitos: 8.1, 8.2, 8.3, 8.4, 8.5, 8.7, 8.8_
  
  - [x] 2.2 Escrever testes unitários para schemas de banco de dados
    - Testar que todas as tabelas têm campos de timestamp
    - Testar que índices estão configurados corretamente
    - _Requisitos: 8.7, 8.8_
  
  - [x] 2.3 Criar script de inicialização do banco de dados
    - Implementar scripts/init_db.py para criar schema
    - _Requisitos: 13.8_

- [x] 3. Implementar módulo de ingestão de dados
  - [x] 3.1 Implementar YahooFinanceClient
    - Criar método fetch_daily_prices para buscar dados de um ticker
    - Criar método fetch_batch_prices para múltiplos tickers
    - Implementar tratamento de erros com DataFetchError
    - _Requisitos: 1.1, 1.6_
  
  - [x] 3.2 Escrever teste de propriedade para YahooFinanceClient
    - **Propriedade 1: Round-trip de Persistência de Dados Brutos**
    - **Valida: Requisitos 1.3, 1.4, 1.5**
  
  - [x] 3.3 Implementar FMPClient
    - Criar métodos para buscar income statement, balance sheet, cash flow, key metrics
    - Implementar autenticação com API key
    - Implementar tratamento de erros
    - _Requisitos: 1.2, 1.6_
  
  - [x] 3.4 Implementar IngestionService
    - Criar método ingest_prices que processa batch de tickers
    - Criar método ingest_fundamentals
    - Implementar persistência em raw_prices_daily e raw_fundamentals
    - Implementar logging de erros sem interromper processamento
    - _Requisitos: 1.3, 1.4, 1.5, 1.6, 1.7_
  
  - [x] 3.5 Escrever teste de propriedade para resiliência a erros
    - **Propriedade 4: Resiliência a Erros de Ingestão**
    - **Valida: Requisitos 1.6, 2.10, 3.8**

- [x] 4. Checkpoint - Validar ingestão de dados
  - Executar testes de ingestão
  - Verificar que dados são salvos corretamente no banco
  - Perguntar ao usuário se há dúvidas ou ajustes necessários

- [x] 5. Implementar cálculo de fatores fundamentalistas
  - [x] 5.1 Implementar FundamentalFactorCalculator
    - Criar métodos para calcular ROE, margem líquida, crescimento de receita 3 anos
    - Criar métodos para calcular dívida/EBITDA, P/L, EV/EBITDA, P/VP
    - Criar método calculate_all_factors que retorna dict com todos os fatores
    - _Requisitos: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7_
  
  - [x] 5.2 Escrever testes unitários para cálculos fundamentalistas
    - Testar cada cálculo com valores conhecidos (exemplos específicos)
    - Testar tratamento de dados faltantes
    - _Requisitos: 2.1-2.7, 2.10_

- [x] 6. Implementar cálculo de fatores de momentum
  - [x] 6.1 Implementar MomentumFactorCalculator
    - Criar métodos para calcular retorno 6m, retorno 12m, RSI 14
    - Criar métodos para calcular volatilidade 90d, drawdown recente
    - Criar método calculate_all_factors que retorna dict com todos os fatores
    - _Requisitos: 3.1, 3.2, 3.3, 3.4, 3.5_
  
  - [x] 6.2 Escrever testes unitários para cálculos de momentum
    - Testar cada cálculo com valores conhecidos
    - Testar casos extremos (RSI em limites, volatilidade zero)
    - Testar tratamento de histórico insuficiente
    - _Requisitos: 3.1-3.5, 3.8_

- [x] 7. Implementar normalização de fatores
  - [x] 7.1 Implementar CrossSectionalNormalizer
    - Criar método normalize_factors que aplica z-score cross-sectional
    - Criar método winsorize para tratar outliers
    - _Requisitos: 2.8, 3.6_
  
  - [x] 7.2 Escrever teste de propriedade para normalização
    - **Propriedade 2: Normalização Cross-Sectional**
    - **Valida: Requisitos 2.8, 3.6**
  
  - [x] 7.3 Implementar persistência de features calculadas
    - Adicionar métodos ao database service para salvar features_daily e features_monthly
    - _Requisitos: 2.9, 3.7_
  
  - [x] 7.4 Escrever teste de propriedade para persistência de features
    - **Propriedade 3: Round-trip de Persistência de Features**
    - **Valida: Requisitos 2.9, 3.7**

- [x] 8. Checkpoint - Validar cálculo e normalização de fatores
  - Executar todos os testes de fatores
  - Verificar que features são salvas corretamente
  - Perguntar ao usuário se há dúvidas ou ajustes necessários

- [x] 9. Implementar motor de scoring
  - [x] 9.1 Implementar ScoringEngine
    - Criar métodos calculate_momentum_score, calculate_quality_score, calculate_value_score
    - Criar método calculate_final_score que aplica pesos configuráveis
    - Criar método score_asset que retorna ScoreResult completo
    - Implementar leitura de pesos do arquivo de configuração
    - _Requisitos: 4.1, 4.2, 4.3, 4.4, 4.7_
  
  - [x] 9.2 Escrever teste de propriedade para cálculo de score ponderado
    - **Propriedade 5: Cálculo de Score Ponderado**
    - **Valida: Requisitos 4.1, 4.2, 4.3, 4.4**
  
  - [x] 9.3 Escrever teste de propriedade para carregamento de configuração
    - **Propriedade 15: Carregamento de Configuração**
    - **Valida: Requisitos 9.1, 9.2**
  
  - [x] 9.4 Implementar persistência de scores
    - Adicionar método ao database service para salvar scores_daily com breakdown
    - _Requisitos: 4.5, 4.6_
  
  - [x] 9.5 Escrever teste de propriedade para persistência de scores
    - **Propriedade 6: Round-trip de Persistência de Scores**
    - **Valida: Requisitos 4.5, 4.6**

- [x] 10. Implementar geração de ranking
  - [x] 10.1 Implementar Ranker
    - Criar método generate_ranking que ordena ativos por score
    - Criar método get_top_n para retornar top N ativos
    - Criar método get_asset_rank para buscar posição de um ticker
    - _Requisitos: 5.1, 5.2, 5.3, 5.4, 5.5_
  
  - [x] 10.2 Escrever teste de propriedade para ordenação de ranking
    - **Propriedade 7: Ordenação de Ranking**
    - **Valida: Requisitos 5.1**
  
  - [x] 10.3 Escrever teste de propriedade para sequencialidade de posições
    - **Propriedade 8: Sequencialidade de Posições no Ranking**
    - **Valida: Requisitos 5.2**
  
  - [x] 10.4 Escrever teste de propriedade para completude de dados
    - **Propriedade 9: Completude de Dados no Ranking**
    - **Valida: Requisitos 5.3, 5.4, 5.5**

- [x] 11. Implementar módulo de confiança (placeholder)
  - [x] 11.1 Implementar ConfidenceEngine com placeholder
    - Criar método calculate_confidence que retorna 0.5 (valor fixo)
    - Estruturar interface para aceitar implementações futuras
    - _Requisitos: 10.1, 10.2, 10.3_
  
  - [x] 11.2 Escrever teste unitário para confidence placeholder
    - Testar que retorna valor padrão 0.5
    - _Requisitos: 10.2_

- [x] 12. Implementar geração de relatórios automáticos
  - [x] 12.1 Implementar ReportGenerator
    - Criar método generate_asset_explanation que gera texto em português
    - Criar métodos auxiliares _identify_top_factors e _identify_bottom_factors
    - Criar método _format_factor_description para converter nomes técnicos
    - _Requisitos: 7.1, 7.2, 7.3, 7.4_
  
  - [x] 12.2 Escrever teste de propriedade para completude de explicações
    - **Propriedade 13: Completude de Explicações Automáticas**
    - **Valida: Requisitos 7.1, 7.2, 7.3, 7.4**

- [x] 13. Checkpoint - Validar scoring, ranking e relatórios
  - Executar todos os testes de scoring e ranking
  - Verificar que explicações são geradas corretamente
  - Perguntar ao usuário se há dúvidas ou ajustes necessários

- [x] 14. Implementar API REST com FastAPI
  - [x] 14.1 Criar schemas Pydantic para API
    - Implementar FactorBreakdown, AssetScore, RankingResponse, AssetDetailResponse, TopAssetsResponse
    - _Requisitos: 6.8_
  
  - [x] 14.2 Implementar endpoint GET /ranking
    - Retornar ranking diário completo ordenado por score
    - Suportar parâmetro opcional de data
    - _Requisitos: 6.1_
  
  - [x] 14.3 Escrever teste de propriedade para endpoint /ranking
    - **Propriedade 10 (parcial): Resposta Completa da API**
    - **Valida: Requisitos 6.1**
  
  - [x] 14.4 Implementar endpoint GET /asset/{ticker}
    - Retornar score, breakdown, posição no ranking, explicação
    - Retornar HTTP 404 para ticker inválido
    - _Requisitos: 6.2, 6.3, 6.4, 6.5, 6.7_
  
  - [x] 14.5 Escrever teste de propriedade para endpoint /asset/{ticker}
    - **Propriedade 10: Resposta Completa da API de Detalhes de Ativo**
    - **Valida: Requisitos 6.2, 6.3, 6.4, 6.5**
  
  - [x] 14.6 Escrever teste unitário para erro 404
    - Testar que ticker inválido retorna 404
    - _Requisitos: 6.7_
  
  - [x] 14.7 Implementar endpoint GET /top
    - Retornar top N ativos por score
    - Suportar parâmetro n (default 10)
    - _Requisitos: 6.6_
  
  - [x] 14.8 Escrever teste de propriedade para endpoint /top
    - **Propriedade 11: Tamanho Correto da Resposta Top N**
    - **Valida: Requisitos 6.6**
  
  - [x] 14.9 Escrever teste de propriedade para formato JSON
    - **Propriedade 12: Formato JSON das Respostas API**
    - **Valida: Requisitos 6.8**
  
  - [x] 14.10 Implementar tratamento de erros e logging na API
    - Configurar exception handlers
    - Configurar logging estruturado
    - _Requisitos: 6.7, 6.8_

- [x] 15. Implementar frontend Streamlit
  - [x] 15.1 Criar página de ranking
    - Implementar tabela ordenável com score, confiança, posição
    - Implementar botão para navegar para detalhes do ativo
    - Consumir endpoint /ranking da API
    - _Requisitos: 11.1, 11.2, 11.3, 11.8_
  
  - [x] 15.2 Criar página de detalhes do ativo
    - Exibir score total e breakdown por categoria
    - Exibir texto de explicação automatizada
    - Exibir gráfico de preço de 12 meses
    - Consumir endpoint /asset/{ticker} da API
    - _Requisitos: 11.4, 11.5, 11.6, 11.7, 11.8_
  
  - [x] 15.3 Escrever teste de propriedade para consumo da API pelo frontend
    - **Propriedade 16: Consumo Correto da API pelo Frontend**
    - **Valida: Requisitos 11.8**

- [x] 16. Implementar script de pipeline completo
  - [x] 16.1 Criar scripts/run_pipeline.py
    - Implementar função run_daily_pipeline que executa todas as etapas
    - Orquestrar ingestão → cálculo de fatores → normalização → scoring → ranking
    - Implementar logging de progresso
    - _Requisitos: 1.1-1.7, 2.1-2.10, 3.1-3.8, 4.1-4.7, 5.1-5.5_
  
  - [x] 16.2 Escrever teste de integração end-to-end
    - Testar pipeline completo com dados de exemplo
    - Verificar que todas as etapas executam sem erros
    - _Requisitos: todos os requisitos funcionais_

- [x] 17. Checkpoint - Validar API e frontend
  - Executar todos os testes de API
  - Testar frontend manualmente
  - Perguntar ao usuário se há dúvidas ou ajustes necessários

- [-] 18. Configurar deployment com Docker
  - [x] 18.1 Criar Dockerfile para backend
    - Configurar imagem Python 3.11
    - Instalar dependências
    - Configurar comando de inicialização com uvicorn
    - _Requisitos: 13.1_
  
  - [x] 18.2 Criar Dockerfile para frontend
    - Configurar imagem Python 3.11
    - Instalar dependências do Streamlit
    - Configurar comando de inicialização
    - _Requisitos: 13.2_
  
  - [x] 18.3 Criar docker-compose.yml
    - Configurar serviços postgres, backend, frontend
    - Configurar variáveis de ambiente
    - Configurar volumes e networks
    - Configurar health checks
    - _Requisitos: 13.3, 13.4, 13.5, 13.6, 13.7_
  
  - [x] 18.4 Testar deployment local com docker-compose
    - Executar docker-compose up
    - Verificar que todos os serviços iniciam corretamente
    - Testar endpoints da API
    - Testar frontend
    - _Requisitos: 13.6, 13.9_

- [x] 19. Criar documentação e exemplos
  - [x] 19.1 Criar README.md
    - Documentar arquitetura do sistema
    - Documentar como executar localmente
    - Documentar como executar com Docker
    - Documentar endpoints da API
    - Documentar variáveis de ambiente
  
  - [x] 19.2 Criar .env.example
    - Incluir todas as variáveis de ambiente necessárias
    - Incluir comentários explicativos
    - _Requisitos: 9.4, 9.5, 13.5_

- [x] 20. Checkpoint final - Validação completa do sistema
  - Executar todos os testes (unitários e de propriedade)
  - Executar pipeline completo com dados reais
  - Validar que ranking é gerado corretamente
  - Validar que API retorna dados corretos
  - Validar que frontend exibe informações corretamente
  - Perguntar ao usuário se o sistema está pronto para uso

## Notas

- Todas as tarefas são obrigatórias para garantir um sistema robusto e bem testado
- Cada tarefa referencia os requisitos específicos que implementa
- Checkpoints garantem validação incremental
- Testes de propriedade validam correção universal
- Testes unitários validam exemplos específicos e casos extremos
- A implementação é incremental: cada etapa constrói sobre a anterior
