# Documento de Requisitos

## Introdução

Este documento especifica os requisitos para um sistema de recomendação quantitativa de ações que combina análise fundamentalista e técnica para gerar rankings diários. O sistema é projetado como base para uma futura startup de research quantitativo, com arquitetura modular e escalável.

## Glossário

- **Sistema**: O sistema completo de ranking quantitativo de ações
- **Módulo_Ingestão**: Componente responsável por coletar dados de preços e fundamentos
- **Motor_Fatores**: Componente que calcula fatores fundamentalistas e técnicos
- **Motor_Scoring**: Componente que combina fatores em score final
- **Servidor_API**: Servidor FastAPI que expõe endpoints REST
- **Frontend**: Interface Streamlit para visualização
- **Banco_Dados**: Banco de dados PostgreSQL
- **Dados_Brutos**: Dados brutos de preços e fundamentos
- **Features**: Fatores calculados e normalizados
- **Score**: Pontuação final de um ativo
- **Ranking**: Lista ordenada de ativos por score
- **Ticker**: Símbolo identificador de uma ação
- **Normalização_Cross_Sectional**: Normalização via z-score comparando todos ativos no mesmo período
- **Fatores_Fundamentalistas**: Fatores baseados em demonstrações financeiras (ROE, margens, etc)
- **Fatores_Momentum**: Fatores baseados em preço e volume (retornos, RSI, volatilidade)
- **Score_Confiança**: Métrica de confiabilidade da recomendação (placeholder na Fase 1)

## Requisitos

### Requisito 1: Ingestão de Dados

**User Story:** Como analista quantitativo, eu quero ingerir dados de preços e fundamentos automaticamente, para que eu possa manter o sistema atualizado com informações recentes.

#### Critérios de Aceitação

1. QUANDO O Módulo_Ingestão solicita dados de preços diários, O Sistema DEVE buscar dados da API Yahoo Finance usando a biblioteca yfinance
2. QUANDO O Módulo_Ingestão solicita dados fundamentalistas, O Sistema DEVE buscar dados da API Financial Modeling Prep
3. QUANDO dados são buscados com sucesso, O Sistema DEVE armazenar dados brutos de preços na tabela raw_prices_daily
4. QUANDO dados fundamentalistas são buscados, O Sistema DEVE armazená-los na tabela raw_fundamentals
5. QUANDO armazena dados brutos, O Sistema DEVE preservar o formato original sem transformações
6. SE a busca de dados falhar para um ticker, ENTÃO O Sistema DEVE registrar o erro e continuar processando outros tickers
7. QUANDO ingere dados para múltiplos tickers, O Sistema DEVE processá-los sequencialmente para evitar rate limiting

### Requisito 2: Cálculo de Fatores Fundamentalistas

**User Story:** Como analista quantitativo, eu quero calcular fatores fundamentalistas mensais, para que eu possa avaliar a qualidade e valor das empresas.

#### Critérios de Aceitação

1. QUANDO calcula fatores fundamentalistas, O Motor_Fatores DEVE computar ROE (Return on Equity)
2. QUANDO calcula fatores fundamentalistas, O Motor_Fatores DEVE computar margem líquida
3. QUANDO calcula fatores fundamentalistas, O Motor_Fatores DEVE computar crescimento de receita de 3 anos
4. QUANDO calcula fatores fundamentalistas, O Motor_Fatores DEVE computar razão Dívida/EBITDA
5. QUANDO calcula fatores fundamentalistas, O Motor_Fatores DEVE computar razão P/L
6. QUANDO calcula fatores fundamentalistas, O Motor_Fatores DEVE computar razão EV/EBITDA
7. QUANDO calcula fatores fundamentalistas, O Motor_Fatores DEVE computar razão P/VP
8. QUANDO fatores fundamentalistas são calculados, O Motor_Fatores DEVE normalizá-los usando z-score cross-sectional dentro do mesmo mês
9. QUANDO armazena fatores calculados, O Sistema DEVE salvá-los na tabela features_monthly
10. SE dados fundamentalistas estão faltando para um ticker, ENTÃO O Motor_Fatores DEVE pular esse ticker e registrar um aviso

### Requisito 3: Cálculo de Fatores de Momentum

**User Story:** Como analista quantitativo, eu quero calcular fatores de momentum diários, para que eu possa capturar tendências de curto e médio prazo.

#### Critérios de Aceitação

1. QUANDO calcula fatores de momentum, O Motor_Fatores DEVE computar retorno de 6 meses
2. QUANDO calcula fatores de momentum, O Motor_Fatores DEVE computar retorno de 12 meses
3. QUANDO calcula fatores de momentum, O Motor_Fatores DEVE computar RSI de 14 períodos
4. QUANDO calcula fatores de momentum, O Motor_Fatores DEVE computar volatilidade de 90 dias
5. QUANDO calcula fatores de momentum, O Motor_Fatores DEVE computar drawdown recente
6. QUANDO fatores de momentum são calculados, O Motor_Fatores DEVE normalizá-los usando z-score cross-sectional dentro do mesmo dia
7. QUANDO armazena fatores calculados, O Sistema DEVE salvá-los na tabela features_daily
8. SE histórico de preços insuficiente existe para um ticker, ENTÃO O Motor_Fatores DEVE pular esse ticker e registrar um aviso

### Requisito 4: Scoring Híbrido

**User Story:** Como analista quantitativo, eu quero combinar fatores fundamentalistas e técnicos em um score único, para que eu possa rankear ações de forma objetiva.

#### Critérios de Aceitação

1. QUANDO calcula o score final, O Motor_Scoring DEVE combinar fatores de momentum com peso 0.4
2. QUANDO calcula o score final, O Motor_Scoring DEVE combinar fatores de qualidade com peso 0.3
3. QUANDO calcula o score final, O Motor_Scoring DEVE combinar fatores de valor com peso 0.3
4. ONDE pesos de fatores são configurados, O Motor_Scoring DEVE ler pesos do arquivo de configuração
5. QUANDO o score final é calculado, O Sistema DEVE armazená-lo na tabela scores_daily com timestamp
6. QUANDO armazena scores, O Sistema DEVE incluir breakdown por categoria de fator
7. QUANDO calcula scores, O Motor_Scoring DEVE usar os fatores fundamentalistas mais recentes disponíveis

### Requisito 5: Geração de Ranking

**User Story:** Como analista quantitativo, eu quero gerar um ranking diário de ações, para que eu possa identificar as melhores oportunidades.

#### Critérios de Aceitação

1. QUANDO gera ranking diário, O Sistema DEVE ordenar todos os ativos por score final em ordem decrescente
2. QUANDO gera ranking, O Sistema DEVE incluir a posição do ativo no ranking
3. QUANDO gera ranking, O Sistema DEVE incluir o score final para cada ativo
4. QUANDO gera ranking, O Sistema DEVE incluir score de confiança para cada ativo
5. QUANDO gera ranking, O Sistema DEVE incluir apenas ativos com dados completos

### Requisito 6: Endpoints REST API

**User Story:** Como desenvolvedor frontend, eu quero acessar dados via API REST, para que eu possa construir interfaces de usuário desacopladas.

#### Critérios de Aceitação

1. QUANDO uma requisição GET é feita para /ranking, O Servidor_API DEVE retornar o ranking diário completo ordenado por score
2. QUANDO uma requisição GET é feita para /asset/{ticker}, O Servidor_API DEVE retornar o score atual para aquele ticker
3. QUANDO uma requisição GET é feita para /asset/{ticker}, O Servidor_API DEVE retornar breakdown de fatores
4. QUANDO uma requisição GET é feita para /asset/{ticker}, O Servidor_API DEVE retornar posição no ranking
5. QUANDO uma requisição GET é feita para /asset/{ticker}, O Servidor_API DEVE retornar texto de explicação automatizada
6. QUANDO uma requisição GET é feita para /top com parâmetro n, O Servidor_API DEVE retornar os top n ativos por score
7. SE um ticker solicitado não existe, ENTÃO O Servidor_API DEVE retornar HTTP 404 com mensagem de erro
8. QUANDO respostas API são geradas, O Servidor_API DEVE retornar dados em formato JSON

### Requisito 7: Geração Automática de Relatórios

**User Story:** Como analista quantitativo, eu quero gerar explicações automáticas para cada ativo, para que eu possa entender rapidamente os drivers do score.

#### Critérios de Aceitação

1. QUANDO gera uma explicação para um ativo, O Sistema DEVE descrever o valor do score final
2. QUANDO gera uma explicação, O Sistema DEVE destacar os fatores positivos mais fortes
3. QUANDO gera uma explicação, O Sistema DEVE destacar os fatores negativos mais fracos
4. QUANDO gera uma explicação, O Sistema DEVE descrever a posição no ranking
5. QUANDO gera uma explicação, O Sistema DEVE usar linguagem natural em português

### Requisito 8: Schema de Banco de Dados

**User Story:** Como desenvolvedor de sistema, eu quero uma estrutura de banco de dados clara e normalizada, para que os dados sejam organizados e consultáveis eficientemente.

#### Critérios de Aceitação

1. O Banco_Dados DEVE conter uma tabela raw_prices_daily para armazenar dados de preços diários
2. O Banco_Dados DEVE conter uma tabela raw_fundamentals para armazenar dados fundamentalistas
3. O Banco_Dados DEVE conter uma tabela features_daily para armazenar fatores calculados diários
4. O Banco_Dados DEVE conter uma tabela features_monthly para armazenar fatores calculados mensais
5. O Banco_Dados DEVE conter uma tabela scores_daily para armazenar scores finais e breakdowns
6. QUANDO armazena dados, O Sistema DEVE manter separação clara entre camadas raw, features e scores
7. QUANDO define tabelas, O Sistema DEVE incluir índices apropriados para performance de consultas
8. QUANDO define tabelas, O Sistema DEVE incluir campos de timestamp para todos os registros

### Requisito 9: Gerenciamento de Configuração

**User Story:** Como analista quantitativo, eu quero configurar pesos de fatores sem modificar código, para que eu possa experimentar diferentes estratégias facilmente.

#### Critérios de Aceitação

1. O Sistema DEVE ler pesos de fatores de um arquivo de configuração
2. ONDE configuração é modificada, O Sistema DEVE aplicar novos pesos no próximo cálculo de scoring
3. QUANDO arquivo de configuração está faltando, O Sistema DEVE usar pesos padrão (0.4 momentum, 0.3 qualidade, 0.3 valor)
4. O Sistema DEVE armazenar credenciais de API no arquivo de configuração
5. O Sistema DEVE armazenar parâmetros de conexão do banco de dados no arquivo de configuração

### Requisito 10: Placeholder de Score de Confiança

**User Story:** Como desenvolvedor de sistema, eu quero uma estrutura preparada para confidence scoring, para que eu possa implementar métricas estatísticas no futuro.

#### Critérios de Aceitação

1. O Sistema DEVE incluir um módulo confidence_engine com implementação placeholder
2. QUANDO calcula confiança, O Sistema DEVE retornar um valor padrão na fase atual
3. QUANDO armazena scores, O Sistema DEVE incluir um campo de confiança no schema do banco de dados
4. O módulo confidence_engine DEVE ser estruturado para aceitar implementações estatísticas futuras

### Requisito 11: Visualização Frontend

**User Story:** Como usuário final, eu quero visualizar rankings e detalhes de ativos em uma interface web, para que eu possa analisar recomendações facilmente.

#### Critérios de Aceitação

1. QUANDO acessa a página de ranking, O Frontend DEVE exibir uma tabela ordenável com todos os ativos
2. QUANDO exibe a tabela de ranking, O Frontend DEVE mostrar score, confiança e posição no ranking
3. QUANDO um usuário clica em um ativo, O Frontend DEVE navegar para a página de detalhes
4. QUANDO acessa a página de detalhes do ativo, O Frontend DEVE exibir o score total
5. QUANDO exibe detalhes do ativo, O Frontend DEVE mostrar breakdown de fatores por categoria
6. QUANDO exibe detalhes do ativo, O Frontend DEVE mostrar texto de explicação automatizada
7. QUANDO exibe detalhes do ativo, O Frontend DEVE mostrar um gráfico de preço de 12 meses
8. QUANDO O Frontend faz requisições, O Frontend DEVE consumir dados dos endpoints REST do Servidor_API

### Requisito 12: Arquitetura Modular

**User Story:** Como desenvolvedor de sistema, eu quero uma arquitetura modular e desacoplada, para que o sistema possa evoluir para incluir backtesting e otimização de portfólio.

#### Critérios de Aceitação

1. O Sistema DEVE separar lógica de ingestão de dados da lógica de cálculo de fatores
2. O Sistema DEVE separar lógica de cálculo de fatores da lógica de scoring
3. O Sistema DEVE separar lógica de scoring da lógica de apresentação da API
4. O Sistema DEVE separar backend do frontend via API REST
5. QUANDO módulos interagem, O Sistema DEVE usar interfaces bem definidas
6. O Sistema DEVE organizar código em diretórios separados por área funcional

### Requisito 13: Deployment e Infraestrutura

**User Story:** Como desenvolvedor de sistema, eu quero preparar a aplicação para deployment em plataformas cloud, para que o deployment seja flexível e escalável.

#### Critérios de Aceitação

1. O Sistema DEVE fornecer um Dockerfile para a aplicação backend compatível com plataformas de container
2. O Sistema DEVE fornecer um Dockerfile para a aplicação frontend compatível com plataformas de container
3. O Sistema DEVE fornecer um arquivo docker-compose.yml para desenvolvimento local
4. O Sistema DEVE suportar conexão com PostgreSQL gerenciado via variáveis de ambiente
5. O Sistema DEVE suportar configuração de credenciais via variáveis de ambiente
6. QUANDO usa docker-compose localmente, O Sistema DEVE iniciar serviços PostgreSQL, backend e frontend
7. QUANDO conecta a banco de dados externo, O Sistema DEVE usar string de conexão fornecida via variável de ambiente
8. O Sistema DEVE incluir script de inicialização de schema do banco de dados
9. O Sistema DEVE ser compatível com deployment em plataformas serverless e tradicionais
