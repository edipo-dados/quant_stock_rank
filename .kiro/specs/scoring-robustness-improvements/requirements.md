# Documento de Requisitos

## Introdução

Este documento especifica melhorias de robustez estrutural no modelo de scoring quantitativo de ações brasileiras. O sistema atual já possui filtros de elegibilidade básicos e um motor de scoring que combina fatores de momentum, qualidade e valor. As melhorias propostas visam aumentar a robustez do modelo através de critérios de exclusão mais rigorosos, ajustes no fator de qualidade para considerar volatilidade de lucros, penalizações graduadas de endividamento, e um mecanismo de distress flag para identificar empresas em situação financeira crítica.

## Glossário

- **Sistema_Scoring**: Motor de scoring que combina fatores normalizados em score final
- **Filtro_Elegibilidade**: Componente que aplica critérios de exclusão antes do scoring
- **Fator_Qualidade**: Score de qualidade baseado em métricas fundamentalistas (ROE, margem líquida, crescimento)
- **ROE**: Return on Equity (Retorno sobre Patrimônio Líquido)
- **EBITDA**: Earnings Before Interest, Taxes, Depreciation and Amortization
- **Dívida_Líquida**: Total Debt - Cash
- **Distress_Flag**: Indicador binário de situação financeira crítica
- **Score_Final**: Score ponderado final após aplicação de todas as penalidades
- **Lucro_Líquido**: Net Income
- **Patrimônio_Líquido**: Shareholders Equity
- **Volatilidade_ROE**: Desvio padrão do ROE em múltiplos períodos

## Requisitos

### Requisito 1: Critérios de Exclusão por Lucratividade

**User Story:** Como analista quantitativo, quero excluir empresas com histórico de prejuízos recentes, para que o universo de investimento contenha apenas empresas com lucratividade consistente.

#### Acceptance Criteria

1. WHEN o lucro líquido do último ano é negativo, THEN o Filtro_Elegibilidade SHALL excluir a empresa do universo
2. WHEN o lucro líquido é negativo em 2 dos últimos 3 anos, THEN o Filtro_Elegibilidade SHALL excluir a empresa do universo
3. WHEN a empresa tem lucro positivo no último ano e em pelo menos 2 dos últimos 3 anos, THEN o Filtro_Elegibilidade SHALL permitir a empresa no universo (sujeito a outros critérios)

### Requisito 2: Critérios de Exclusão por Estrutura de Capital

**User Story:** Como analista quantitativo, quero excluir empresas com patrimônio líquido não positivo, para que o universo contenha apenas empresas com estrutura de capital saudável.

#### Acceptance Criteria

1. WHEN o patrimônio líquido é menor ou igual a zero, THEN o Filtro_Elegibilidade SHALL excluir a empresa do universo
2. WHEN o patrimônio líquido é positivo, THEN o Filtro_Elegibilidade SHALL permitir a empresa no universo (sujeito a outros critérios)

### Requisito 3: Critérios de Exclusão por Endividamento Extremo

**User Story:** Como analista quantitativo, quero excluir empresas com endividamento extremo, para que o universo contenha apenas empresas com níveis de dívida gerenciáveis.

#### Acceptance Criteria

1. WHEN a razão Dívida_Líquida / EBITDA é maior que 8, THEN o Filtro_Elegibilidade SHALL excluir a empresa do universo
2. WHEN a razão Dívida_Líquida / EBITDA é menor ou igual a 8, THEN o Filtro_Elegibilidade SHALL permitir a empresa no universo (sujeito a outros critérios)
3. WHEN o EBITDA é menor ou igual a zero, THEN o Sistema_Scoring SHALL tratar a razão como infinita para fins de comparação com o limite
4. WHERE a empresa é uma instituição financeira (banco), o Sistema_Scoring SHALL aplicar tratamento especial conforme lógica existente

### Requisito 4: ROE Robusto com Média de 3 Anos

**User Story:** Como analista quantitativo, quero usar ROE médio de 3 anos no fator de qualidade, para que o score reflita rentabilidade sustentável ao invés de picos temporários.

#### Acceptance Criteria

1. WHEN há dados de lucro líquido e patrimônio líquido para os últimos 3 anos, THEN o Sistema_Scoring SHALL calcular ROE para cada ano
2. WHEN há ROEs calculados para múltiplos anos, THEN o Sistema_Scoring SHALL calcular a média aritmética dos ROEs
3. WHEN há menos de 3 anos de dados mas pelo menos 2 anos, THEN o Sistema_Scoring SHALL calcular a média com os dados disponíveis
4. WHEN há menos de 2 anos de dados, THEN o Sistema_Scoring SHALL usar o ROE do período mais recente

### Requisito 5: Penalização de Volatilidade do ROE

**User Story:** Como analista quantitativo, quero penalizar empresas com ROE volátil, para que o score favoreça empresas com rentabilidade estável.

#### Acceptance Criteria

1. WHEN há dados de ROE para múltiplos períodos, THEN o Sistema_Scoring SHALL calcular o desvio padrão do ROE
2. WHEN o desvio padrão do ROE é calculado, THEN o Sistema_Scoring SHALL calcular ROE_ajustado = ROE_mean - (0.5 * ROE_std)
3. WHEN o ROE_ajustado é calculado, THEN o Sistema_Scoring SHALL usar ROE_ajustado no cálculo do Fator_Qualidade
4. WHEN não há dados suficientes para calcular desvio padrão (menos de 2 períodos), THEN o Sistema_Scoring SHALL usar ROE_mean sem ajuste

### Requisito 6: Penalização por Prejuízo Recente

**User Story:** Como analista quantitativo, quero penalizar fortemente empresas com prejuízo no último ano, para que o score reflita o risco de lucratividade recente negativa.

#### Acceptance Criteria

1. WHEN o lucro líquido do último ano é negativo, THEN o Sistema_Scoring SHALL multiplicar o quality_score por 0.4
2. WHEN o lucro líquido do último ano é positivo ou zero, THEN o Sistema_Scoring SHALL manter o quality_score sem esta penalização
3. WHEN a penalização é aplicada, THEN o Sistema_Scoring SHALL registrar a penalização nos metadados do score

### Requisito 7: Penalização Graduada de Endividamento

**User Story:** Como analista quantitativo, quero aplicar penalizações graduadas baseadas no nível de endividamento, para que o score reflita diferentes níveis de risco financeiro.

#### Acceptance Criteria

1. WHEN a razão Dívida_Líquida / EBITDA é maior que 3 e menor ou igual a 5, THEN o Sistema_Scoring SHALL aplicar penalização leve ao quality_score
2. WHEN a razão Dívida_Líquida / EBITDA é maior que 5 e menor ou igual a 8, THEN o Sistema_Scoring SHALL aplicar penalização forte ao quality_score
3. WHEN a razão Dívida_Líquida / EBITDA é menor ou igual a 3, THEN o Sistema_Scoring SHALL não aplicar penalização de endividamento
4. WHEN a razão Dívida_Líquida / EBITDA é maior que 8, THEN a empresa SHALL ser excluída pelo Filtro_Elegibilidade (conforme Requisito 3)
5. WHEN penalizações são aplicadas, THEN o Sistema_Scoring SHALL registrar o tipo e magnitude da penalização nos metadados

### Requisito 8: Distress Flag

**User Story:** Como analista quantitativo, quero identificar empresas em situação de distress financeiro, para que o score final reflita o risco elevado dessas empresas.

#### Acceptance Criteria

1. WHEN uma empresa atende a qualquer critério de distress, THEN o Sistema_Scoring SHALL ativar o distress_flag
2. WHEN o distress_flag está ativado, THEN o Sistema_Scoring SHALL multiplicar o score_final por 0.5
3. WHEN o distress_flag está desativado, THEN o Sistema_Scoring SHALL manter o score_final sem esta penalização
4. WHEN o distress_flag é ativado, THEN o Sistema_Scoring SHALL registrar os critérios que ativaram o flag nos metadados

### Requisito 9: Critérios de Ativação do Distress Flag

**User Story:** Como analista quantitativo, quero definir critérios claros para ativação do distress flag, para que a identificação de empresas em distress seja consistente e objetiva.

#### Acceptance Criteria

1. WHEN o lucro líquido do último ano é negativo, THEN o Sistema_Scoring SHALL ativar o distress_flag
2. WHEN o lucro líquido é negativo em 2 dos últimos 3 anos, THEN o Sistema_Scoring SHALL ativar o distress_flag
3. WHEN a razão Dívida_Líquida / EBITDA é maior que 5, THEN o Sistema_Scoring SHALL ativar o distress_flag
4. WHEN o patrimônio líquido é menor ou igual a zero, THEN a empresa SHALL ser excluída antes do scoring (conforme Requisito 2)
5. WHEN múltiplos critérios de distress são atendidos, THEN o Sistema_Scoring SHALL registrar todos os critérios nos metadados

### Requisito 10: Persistência de Metadados de Robustez

**User Story:** Como analista quantitativo, quero armazenar metadados sobre as melhorias de robustez aplicadas, para que eu possa auditar e analisar as decisões do modelo.

#### Acceptance Criteria

1. WHEN um score é calculado, THEN o Sistema_Scoring SHALL persistir o distress_flag no banco de dados
2. WHEN penalizações são aplicadas, THEN o Sistema_Scoring SHALL persistir um dicionário JSON com todas as penalizações aplicadas
3. WHEN uma empresa é excluída, THEN o Filtro_Elegibilidade SHALL persistir as razões de exclusão
4. WHEN dados são persistidos, THEN o Sistema_Scoring SHALL incluir campos: distress_flag (boolean), distress_reasons (JSON), debt_penalties (JSON)

### Requisito 11: Compatibilidade com Sistema Existente

**User Story:** Como desenvolvedor, quero que as melhorias sejam compatíveis com o sistema existente, para que a integração seja suave e não quebre funcionalidades existentes.

#### Acceptance Criteria

1. WHEN as melhorias são implementadas, THEN o Sistema_Scoring SHALL manter compatibilidade com a interface existente de score_asset_enhanced
2. WHEN novos campos são adicionados ao banco de dados, THEN o Sistema_Scoring SHALL fornecer valores padrão para registros existentes
3. WHEN instituições financeiras são processadas, THEN o Sistema_Scoring SHALL manter o tratamento especial existente para EBITDA
4. WHEN os testes existentes são executados, THEN o Sistema_Scoring SHALL passar em todos os testes de propriedade e unidade existentes
