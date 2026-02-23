# Chat com Gemini - Assistente Conversacional

Interface conversacional para análise de ações brasileiras usando Google Gemini 2.5 Flash.

## 🎯 Visão Geral

O Chat Assistente permite que você converse naturalmente sobre ações brasileiras. O assistente tem acesso direto ao sistema de ranking e pode:

- Responder perguntas sobre ações específicas
- Fazer comparações entre ativos
- Buscar ações por critérios
- Analisar histórico de preços
- Explicar scores e rankings
- Fornecer insights baseados em dados
- **Buscar notícias e informações externas na web**
- **Consultar fontes especializadas brasileiras:**
  - Status Invest (indicadores fundamentalistas)
  - Investidor10 (dividendos e resultados)
  - InfoMoney (análises e gráficos)
  - Investing.com (cotação em tempo real)
  - Google Finance (histórico de performance)

## 🚀 Como Usar

### 1. Obter API Key do Gemini

1. Acesse: https://makersuite.google.com/app/apikey
2. Faça login com sua conta Google
3. Clique em "Create API Key"
4. Copie a API key gerada

**Nota**: A API do Gemini é gratuita para uso pessoal com limites generosos.

### 2. Acessar o Chat

1. Inicie a aplicação:
```bash
docker-compose up -d
```

2. Acesse o frontend: http://localhost:8501

3. Navegue para a página "💬 Chat Assistente" (primeira página)

4. Cole sua API Key do Gemini na barra lateral

5. Comece a conversar!

## 💬 Exemplos de Conversas

### Análise Básica

```
Você: Quais são as 5 melhores ações para investir?

Assistente: Vou buscar as top 5 ações do ranking atual...

As 5 melhores ações hoje são:

1. CYRE3.SA - Score: 0.333
   - Momentum: 0.22 (moderado)
   - Qualidade: 0.34 (bom)
   - Valor: 0.44 (excelente)

2. PRIO3.SA - Score: 0.321
   - Momentum: 0.50 (forte)
   - Qualidade: 0.29 (moderado)
   - Valor: 0.17 (razoável)

[...]

Recomendo analisar cada uma individualmente antes de investir.
```

### Análise Detalhada

```
Você: Me fale sobre PETR4.SA

Assistente: Vou buscar os detalhes de PETR4.SA...

PETR4.SA está na posição #12 do ranking com score final de 0.245.

📊 Breakdown de Scores:
- Momentum: 0.42 (forte tendência de alta)
- Qualidade: 0.31 (fundamentos sólidos)
- Valor: -0.08 (um pouco cara no momento)

✅ Pontos Fortes:
- Retorno de 12 meses acima da média
- ROE consistente nos últimos 3 anos
- Volatilidade controlada

⚠️ Pontos de Atenção:
- P/L um pouco elevado
- Drawdown recente de 5%

A ação tem bom momentum e qualidade, mas está um pouco cara.
Pode ser interessante aguardar uma correção para entrada.
```

### Comparação

```
Você: Compare PETR4.SA com VALE3.SA

Assistente: Vou comparar essas duas ações...

Comparação PETR4.SA vs VALE3.SA:

PETR4.SA (#12):
- Score Final: 0.245
- Momentum: 0.42 ⭐
- Qualidade: 0.31
- Valor: -0.08

VALE3.SA (#8):
- Score Final: 0.267 ⭐
- Momentum: 0.38
- Qualidade: 0.45 ⭐
- Valor: 0.02 ⭐

Análise:
- VALE3.SA tem score geral melhor (0.267 vs 0.245)
- PETR4.SA tem momentum mais forte
- VALE3.SA tem qualidade superior
- VALE3.SA está mais barata (melhor valor)

Conclusão: VALE3.SA parece mais atrativa no momento,
com melhor equilíbrio entre qualidade e valor.
```

### Busca por Critérios

```
Você: Quais ações têm momentum forte e qualidade boa?

Assistente: Vou buscar ações com momentum >0.5 e qualidade >0.4...

Encontrei 8 ações que atendem esses critérios:

1. GGBR4.SA
   - Momentum: 0.67 (muito forte)
   - Qualidade: 0.52 (boa)
   - Posição: #3

2. PRIO3.SA
   - Momentum: 0.58 (forte)
   - Qualidade: 0.48 (boa)
   - Posição: #2

[...]

Essas ações combinam tendência de alta forte com
fundamentos sólidos, sendo boas candidatas para análise.
```

### Histórico de Preços

```
Você: Como está o preço de PETR4.SA nos últimos 30 dias?

Assistente: Vou buscar o histórico de preços...

Histórico de PETR4.SA (últimos 30 dias):

- Preço atual: R$ 38.50
- Variação 30 dias: +5.2%
- Máxima: R$ 39.80
- Mínima: R$ 36.20
- Volatilidade: Moderada

Tendência: Alta consistente com pequenas correções.
O preço está próximo da máxima do período.
```

## 🛠️ Funcionalidades Técnicas

### Ferramentas Disponíveis

O assistente tem acesso a 6 ferramentas:

1. **get_ranking**: Ranking completo de ações
2. **get_top_stocks**: Top N melhores ações
3. **get_asset_details**: Detalhes de um ativo
4. **get_price_history**: Histórico de preços
5. **compare_assets**: Comparação entre ativos
6. **search_by_criteria**: Busca por critérios

### Function Calling

O Gemini usa "function calling" para acessar as ferramentas:

1. Usuário faz uma pergunta
2. Gemini identifica qual ferramenta usar
3. Sistema executa a ferramenta
4. Gemini recebe os dados
5. Gemini formula resposta em linguagem natural

### Contexto de Conversa

- Cada sessão mantém histórico completo
- O assistente lembra de conversas anteriores
- Você pode fazer perguntas de follow-up
- Contexto é mantido até limpar o chat

### Consulta a Fontes Externas

```
Você: Quero mais informações sobre PETR4

Assistente: Vou buscar informações em múltiplas fontes...

Aqui estão os links para análise completa de PETR4:

📊 Status Invest: https://statusinvest.com.br/acoes/petr4
   → Indicadores fundamentalistas, DY, P/L, ROE, margem líquida

💰 Investidor10: https://investidor10.com.br/acoes/petr4
   → Histórico de dividendos, resultados trimestrais

📈 InfoMoney: https://www.infomoney.com.br/cotacoes/b3/acao/petr4
   → Gráficos interativos, notícias e análises

⏱️ Investing.com: https://br.investing.com/equities/petr4
   → Cotação em tempo real e análises técnicas

🔍 Google Finance: https://www.google.com/finance/quote/PETR4:BVMF
   → Cotação em tempo real e histórico

Recomendo consultar múltiplas fontes para uma análise completa!
```

### Busca de Notícias

```
Você: Tem alguma notícia recente sobre PRIO3?

Assistente: Vou buscar notícias recentes sobre PRIO3...

Encontrei 5 notícias recentes:

1. "PRIO anuncia novo projeto de exploração no pré-sal"
   Fonte: InfoMoney
   Link: [...]

2. "Ações da PRIO sobem 5% após resultados do 4T"
   Fonte: Valor Econômico
   Link: [...]

[...]
```

## ⚙️ Configuração

### Variáveis de Ambiente

Opcionalmente, configure a API key no `.env`:

```env
GEMINI_API_KEY=sua-api-key-aqui
```

### Limites da API

Gemini Free Tier:
- 60 requisições por minuto
- 1500 requisições por dia
- Suficiente para uso pessoal

### Timeout

O timeout padrão é 60 segundos. Para ajustar:

```python
# Em frontend/pages/1_💬_Chat_Assistente.py
response = requests.post(..., timeout=120)  # 2 minutos
```

## 🔒 Segurança

### API Key

- Nunca compartilhe sua API key
- Não commite a key no Git
- Use variáveis de ambiente em produção
- Revogue keys comprometidas

### Dados

- O chat não armazena dados permanentemente
- Histórico é mantido apenas na sessão
- Limpar chat remove todos os dados
- API key não é enviada para o backend (apenas para Gemini)

## 🐛 Troubleshooting

### "Configure sua API Key"

**Causa**: API key não foi fornecida.

**Solução**: Cole sua API key na barra lateral.

### "Erro 401: Unauthorized"

**Causa**: API key inválida ou expirada.

**Solução**: 
1. Verifique se copiou a key corretamente
2. Gere uma nova key em https://makersuite.google.com/app/apikey

### "Erro 429: Too Many Requests"

**Causa**: Excedeu limite de requisições.

**Solução**: Aguarde alguns minutos e tente novamente.

### "Timeout"

**Causa**: Requisição demorou muito.

**Solução**: 
1. Verifique se a API está rodando
2. Tente uma pergunta mais simples
3. Aguarde e tente novamente

### Resposta Genérica

**Causa**: Assistente não usou as ferramentas.

**Solução**: Seja mais específico:
- ❌ "Me fale sobre ações"
- ✅ "Quais são as top 5 ações?"
- ✅ "Me fale sobre PETR4.SA"

## 📊 Exemplos de Perguntas

### Ranking e Top Ações

```
- Quais são as 10 melhores ações?
- Me mostre o ranking completo
- Quais ações estão no top 20?
- Qual é a melhor ação hoje?
```

### Análise de Ativo

```
- Me fale sobre PETR4.SA
- Analise VALE3.SA para mim
- Como está ITUB4.SA?
- Quais são os pontos fortes de BBDC4.SA?
```

### Comparações

```
- Compare PETR4.SA com VALE3.SA
- Qual é melhor: ITUB4.SA ou BBDC4.SA?
- Compare as 3 maiores petroleiras
- PETR4.SA vs PRIO3.SA, qual escolher?
```

### Busca por Critérios

```
- Quais ações têm momentum forte?
- Me mostre ações com qualidade alta
- Busque ações baratas (valor alto)
- Ações com score acima de 0.3
```

### Histórico e Preços

```
- Como está o preço de PETR4.SA?
- Mostre o histórico de VALE3.SA
- Preços de ITUB4.SA nos últimos 30 dias
- Qual a variação de BBDC4.SA?
```

### Análises Complexas

```
- Quais ações têm momentum forte E qualidade boa?
- Me recomende 3 ações para investir agora
- Qual setor está melhor no ranking?
- Ações defensivas com bom valor
```

## 🚀 Próximos Passos

### Melhorias Futuras

- [ ] Suporte a gráficos no chat
- [ ] Análise de portfólio
- [ ] Alertas personalizados
- [ ] Histórico persistente
- [ ] Exportar conversas
- [ ] Suporte a voz
- [ ] Análise técnica avançada

### Contribuindo

Sugestões de melhorias são bem-vindas! Abra uma issue no GitHub.

## 📚 Referências

- [Google Gemini API](https://ai.google.dev/)
- [Gemini Function Calling](https://ai.google.dev/docs/function_calling)
- [API Documentation](http://localhost:8000/docs)
- [Guia de Uso](docs/GUIA_USO.md)

---

**Nota**: Este assistente fornece informações baseadas em dados quantitativos.
Não constitui recomendação de investimento. Sempre consulte um profissional
qualificado antes de tomar decisões de investimento.
