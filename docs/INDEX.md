# 📚 Índice da Documentação - v2.6.0

Bem-vindo à documentação do Sistema de Ranking Quantitativo de Ações!

## 📌 Versão Atual: 2.6.0 - Adaptive History

Sistema com histórico adaptativo e confidence factors:
- **Histórico Adaptativo**: Usa 1-3 anos de dados sem exigir exatamente 3 anos
- **Confidence Factors**: Rastreia qualidade dos dados e aplica ao quality_score
- Scores distribuídos entre -3 e +3, média ~0
- Taxa de elegibilidade >= 80-90%
- Pipeline determinístico e estatisticamente estável

## 🚀 Início Rápido

**Novo no sistema?** Comece aqui:
1. [README.md](../README.md) - Visão geral e instalação
2. [GUIA_USO.md](GUIA_USO.md) - Tutorial completo de uso
3. [ADAPTIVE_HISTORY_IMPLEMENTATION.md](../ADAPTIVE_HISTORY_IMPLEMENTATION.md) - **NOVO**: Histórico adaptativo
4. [DOCKER.md](DOCKER.md) - Guia Docker

## 📖 Documentação Principal

### Para Usuários

| Documento | Descrição | Quando Usar |
|-----------|-----------|-------------|
| [README.md](../README.md) | Visão geral do sistema | Primeira leitura |
| [GUIA_USO.md](GUIA_USO.md) | Tutorial completo | Aprender a usar |
| [CALCULOS_RANKING.md](CALCULOS_RANKING.md) | Metodologia detalhada | Entender cálculos |
| [ADAPTIVE_HISTORY_IMPLEMENTATION.md](../ADAPTIVE_HISTORY_IMPLEMENTATION.md) | **NOVO v2.6.0**: Histórico adaptativo | Entender confidence factors |
| [PIPELINE_ARCHITECTURE.md](PIPELINE_ARCHITECTURE.md) | Arquitetura 3 camadas | Entender pipeline |
| [MISSING_VALUE_TREATMENT.md](MISSING_VALUE_TREATMENT.md) | Tratamento de NaN | Entender imputação |
| [DOCKER.md](DOCKER.md) | Guia completo Docker | Usar Docker |
| [CHAT_GEMINI.md](CHAT_GEMINI.md) | Chat com IA | Usar assistente |
| [MCP_SERVER.md](MCP_SERVER.md) | Integração com agentes | Integrar com IA |

### Para Deploy e Manutenção

| Documento | Descrição |
|-----------|-----------|
| [../deploy/EC2_DEPLOY_V2.6.0.md](../deploy/EC2_DEPLOY_V2.6.0.md) | **NOVO**: Deploy v2.6.0 no EC2 |
| [../deploy/SETUP_NOVO_EC2.md](../deploy/SETUP_NOVO_EC2.md) | Setup inicial EC2 |
| [../deploy/QUICK_REFERENCE.md](../deploy/QUICK_REFERENCE.md) | Comandos rápidos |
| [CHANGELOG.md](../CHANGELOG.md) | Histórico de mudanças |

### Para Desenvolvedores

| Documento | Descrição |
|-----------|-----------|
| [ACADEMIC_MOMENTUM_IMPLEMENTATION.md](ACADEMIC_MOMENTUM_IMPLEMENTATION.md) | Momentum acadêmico |
| [VALUE_SIZE_IMPLEMENTATION.md](VALUE_SIZE_IMPLEMENTATION.md) | Fatores Value e Size |
| [MELHORIAS_ACADEMICAS.md](MELHORIAS_ACADEMICAS.md) | Roadmap de melhorias |
| [API Swagger](http://localhost:8000/docs) | Documentação interativa da API |
| [API ReDoc](http://localhost:8000/redoc) | Documentação alternativa |

## 🎯 Busca por Caso de Uso

### "Quero instalar e rodar"
→ [README.md - Início Rápido](../README.md#-início-rápido)

### "Quero usar o sistema"
→ [GUIA_USO.md](GUIA_USO.md)

### "Quero entender os cálculos"
→ [CALCULOS_RANKING.md](CALCULOS_RANKING.md)

### "Quero entender o histórico adaptativo (v2.6.0)"
→ [ADAPTIVE_HISTORY_IMPLEMENTATION.md](../ADAPTIVE_HISTORY_IMPLEMENTATION.md)

### "Quero fazer deploy no EC2"
→ [../deploy/EC2_DEPLOY_V2.6.0.md](../deploy/EC2_DEPLOY_V2.6.0.md)

### "Quero usar Docker"
→ [DOCKER.md](DOCKER.md)

### "Quero conversar com IA sobre ações"
→ [CHAT_GEMINI.md](CHAT_GEMINI.md)

### "Quero integrar com Claude/ChatGPT"
→ [MCP_SERVER.md](MCP_SERVER.md)

### "Tenho problemas"
→ [ADAPTIVE_HISTORY_IMPLEMENTATION.md - Troubleshooting](../ADAPTIVE_HISTORY_IMPLEMENTATION.md#troubleshooting)

## 📊 Estrutura da Documentação

```
docs/
├── INDEX.md                              # Este arquivo
├── GUIA_USO.md                          # Tutorial completo
├── CALCULOS_RANKING.md                  # Metodologia
├── ADAPTIVE_HISTORY_IMPLEMENTATION.md   # NOVO v2.6.0: Histórico adaptativo
├── PIPELINE_ARCHITECTURE.md             # Arquitetura 3 camadas
├── MISSING_VALUE_TREATMENT.md           # Tratamento de NaN
├── ACADEMIC_MOMENTUM_IMPLEMENTATION.md  # Momentum acadêmico
├── VALUE_SIZE_IMPLEMENTATION.md         # Value e Size
├── MELHORIAS_ACADEMICAS.md             # Roadmap
├── DOCKER.md                           # Guia Docker
├── CHAT_GEMINI.md                      # Chat com IA
└── MCP_SERVER.md                       # Integração MCP

deploy/
├── EC2_DEPLOY_V2.6.0.md                # NOVO: Deploy v2.6.0
├── SETUP_NOVO_EC2.md                   # Setup inicial
└── QUICK_REFERENCE.md                  # Comandos rápidos
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
- 🆕 Novo na v2.6.0

### Formato de Tickers
Sempre use o formato completo com `.SA`:
- ✅ Correto: `PETR4.SA`, `VALE3.SA`, `ITUB4.SA`
- ❌ Errado: `PETR4`, `VALE3`, `ITUB4`

## 🆘 Suporte

### Problemas Técnicos
1. Consulte [ADAPTIVE_HISTORY_IMPLEMENTATION.md - Troubleshooting](../ADAPTIVE_HISTORY_IMPLEMENTATION.md#troubleshooting)
2. Veja logs: `docker logs quant-ranker-backend --tail 50`
3. Abra issue no GitHub

### Dúvidas sobre Uso
1. Leia [GUIA_USO.md](GUIA_USO.md)
2. Consulte [CALCULOS_RANKING.md](CALCULOS_RANKING.md)
3. Veja exemplos na [API Swagger](http://localhost:8000/docs)

### Dúvidas sobre v2.6.0
1. Leia [ADAPTIVE_HISTORY_IMPLEMENTATION.md](../ADAPTIVE_HISTORY_IMPLEMENTATION.md)
2. Veja [CHANGELOG.md](../CHANGELOG.md) seção v2.6.0
3. Consulte [../deploy/EC2_DEPLOY_V2.6.0.md](../deploy/EC2_DEPLOY_V2.6.0.md) para deploy

## 📅 Última Atualização

26 de Fevereiro de 2026 - v2.6.0

### Mudanças Principais v2.6.0
- 🆕 **Histórico Adaptativo**: Sistema usa 1-3 anos de dados
- 🆕 **Confidence Factors**: Rastreia qualidade dos dados
- 🆕 **Scores Melhorados**: Menos NaN, mais ativos elegíveis
- 🆕 **Instituições Financeiras**: Scores calculados corretamente
- 🆕 **Taxa de Elegibilidade**: 60-70% → 80-90%

### Mudanças Anteriores
- ✅ Arquitetura de 3 camadas (v2.5.1)
- ✅ Tratamento estatístico de missing values (v2.5.2)
- ✅ Remoção completa de valores sentinela (-999)
- ✅ Scores normalizados corretamente

## 🔄 Migração para v2.6.0

Se você está usando v2.5.2, siga estes passos:

1. **Backup do banco de dados**
   ```bash
   ./deploy/backup-db.sh
   ```

2. **Pull das mudanças**
   ```bash
   git pull origin main
   ```

3. **Rebuild containers**
   ```bash
   docker-compose down
   docker-compose build backend
   docker-compose up -d
   ```

4. **Executar migration**
   ```bash
   docker exec quant-ranker-backend python scripts/migrate_add_confidence_factors.py
   ```

5. **Executar pipeline**
   ```bash
   docker exec quant-ranker-backend python scripts/run_pipeline_docker.py --mode liquid --limit 50
   ```

6. **Verificar scores**
   ```bash
   docker exec quant-ranker-backend python scripts/check_latest_scores.py
   ```

Veja [../deploy/EC2_DEPLOY_V2.6.0.md](../deploy/EC2_DEPLOY_V2.6.0.md) para procedimento completo.

---

**Boa sorte e bons investimentos! 🚀📈**
