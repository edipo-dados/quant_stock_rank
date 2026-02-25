# 📚 Índice da Documentação

Bem-vindo à documentação do Sistema de Ranking Quantitativo de Ações!

## 🚀 Início Rápido

**Novo no sistema?** Comece aqui:
1. [README.md](../README.md) - Visão geral e instalação
2. [GUIA_USO.md](GUIA_USO.md) - Tutorial completo de uso
3. [DOCKER.md](DOCKER.md) - Guia Docker

## 📖 Documentação Principal

### Para Usuários

| Documento | Descrição | Quando Usar |
|-----------|-----------|-------------|
| [README.md](../README.md) | Visão geral do sistema | Primeira leitura |
| [GUIA_USO.md](GUIA_USO.md) | Tutorial completo | Aprender a usar |
| [CALCULOS_RANKING.md](CALCULOS_RANKING.md) | Metodologia detalhada | Entender cálculos |
| [MELHORIAS_ACADEMICAS.md](MELHORIAS_ACADEMICAS.md) | Melhorias acadêmicas v2.2.0 | Entender mudanças |
| [DOCKER.md](DOCKER.md) | Guia completo Docker | Usar Docker |
| [CHAT_GEMINI.md](CHAT_GEMINI.md) | Chat com IA | Usar assistente |
| [MCP_SERVER.md](MCP_SERVER.md) | Integração com agentes | Integrar com IA |
| [PIPELINE_INTELIGENTE.md](PIPELINE_INTELIGENTE.md) | Pipeline otimizado | Executar pipeline |

### Para Desenvolvedores

| Documento | Descrição |
|-----------|-----------|
| [CHANGELOG.md](../CHANGELOG.md) | Histórico de mudanças |
| [API Swagger](http://localhost:8000/docs) | Documentação interativa da API |
| [API ReDoc](http://localhost:8000/redoc) | Documentação alternativa |

## 🎯 Busca por Caso de Uso

### "Quero instalar e rodar"
→ [README.md - Início Rápido](../README.md#-início-rápido)

### "Quero usar o sistema"
→ [GUIA_USO.md](GUIA_USO.md)

### "Quero entender os cálculos"
→ [CALCULOS_RANKING.md](CALCULOS_RANKING.md)

### "Quero usar Docker"
→ [DOCKER.md](DOCKER.md)

### "Quero conversar com IA sobre ações"
→ [CHAT_GEMINI.md](CHAT_GEMINI.md)

### "Quero integrar com Claude/ChatGPT"
→ [MCP_SERVER.md](MCP_SERVER.md)

### "Quero executar o pipeline"
→ [PIPELINE_INTELIGENTE.md](PIPELINE_INTELIGENTE.md)


### "Tenho problemas"
→ [GUIA_USO.md - Troubleshooting](GUIA_USO.md#8-troubleshooting)

## 📊 Estrutura da Documentação

```
docs/
├── INDEX.md                    # Este arquivo
├── GUIA_USO.md                # Tutorial completo
├── CALCULOS_RANKING.md        # Metodologia
├── MELHORIAS_ACADEMICAS.md    # Melhorias acadêmicas v2.2.0
├── DOCKER.md                  # Guia Docker
├── CHAT_GEMINI.md             # Chat com IA
├── MCP_SERVER.md              # Integração MCP
└── PIPELINE_INTELIGENTE.md    # Pipeline otimizado
```

## 🔗 Links Úteis

### Aplicação
- Frontend: http://localhost:8501
- API Swagger: http://localhost:8000/docs
- API ReDoc: http://localhost:8000/redoc
- Health Check: http://localhost:8000/health

### Repositório
- GitHub: https://github.com/edipo-dados/quant_stock_rank
- Issues: https://github.com/edipo-dados/quant_stock_rank/issues

### Recursos Externos
- Yahoo Finance: https://finance.yahoo.com
- Google Gemini API: https://makersuite.google.com/app/apikey
- B3 (Bolsa Brasil): https://www.b3.com.br

## 📝 Convenções

### Símbolos Usados
- ✅ Implementado/Funcionando
- ⚠️ Atenção/Cuidado
- 🐛 Bug/Problema
- 🔧 Configuração
- 📊 Dados/Métricas
- 🚀 Performance/Otimização

### Formato de Tickers
Sempre use o formato completo com `.SA`:
- ✅ Correto: `PETR4.SA`, `VALE3.SA`, `ITUB4.SA`
- ❌ Errado: `PETR4`, `VALE3`, `ITUB4`

## 🆘 Suporte

### Problemas Técnicos
1. Consulte [GUIA_USO.md - Troubleshooting](GUIA_USO.md#8-troubleshooting)
2. Veja logs: `docker logs quant-ranker-backend --tail 50`
3. Abra issue no GitHub

### Dúvidas sobre Uso
1. Leia [GUIA_USO.md](GUIA_USO.md)
2. Consulte [CALCULOS_RANKING.md](CALCULOS_RANKING.md)
3. Veja exemplos na [API Swagger](http://localhost:8000/docs)

## 📅 Última Atualização

24 de Fevereiro de 2026 - v2.2.0 (Melhorias Acadêmicas)

---

**Boa sorte e bons investimentos! 🚀📈**
