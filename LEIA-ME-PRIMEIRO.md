# 📖 LEIA-ME PRIMEIRO

## Bem-vindo ao Sistema de Ranking Quantitativo!

Este documento é seu ponto de partida. Leia-o primeiro para entender como navegar na documentação.

---

## 🎯 O que é este sistema?

Um sistema automatizado que analisa e rankeia ações brasileiras usando fatores quantitativos:
- **Momentum** (40%): Tendências de preço
- **Qualidade** (30%): Fundamentos financeiros
- **Valor** (30%): Atratividade de valuation

**Resultado**: Ranking objetivo das ações mais atrativas.

---

## 🚀 Início Rápido (5 minutos)

### Opção 1: Docker (Recomendado)

```bash
# 1. Clone e entre na pasta
git clone https://github.com/edipo-dados/quant_stock_rank.git
cd quant_stock_rank

# 2. Inicie tudo
docker-compose up -d

# 3. Inicialize o banco
docker-compose exec backend python scripts/init_db.py

# 4. Execute o pipeline (5 ativos de teste)
docker-compose exec backend python scripts/run_pipeline_docker.py --mode test

# 5. Acesse
# Frontend: http://localhost:8501
# API: http://localhost:8000/docs
```

### Opção 2: Local

```bash
# 1. Clone e entre na pasta
git clone https://github.com/edipo-dados/quant_stock_rank.git
cd quant_stock_rank

# 2. Instale
pip install -r requirements.txt

# 3. Configure
cp .env.example .env
# Edite .env: DATABASE_URL=sqlite:///./quant_ranker.db

# 4. Inicialize
python scripts/init_db.py
python scripts/run_pipeline.py --mode test

# 5. Execute (2 terminais)
python app/main.py                    # Terminal 1
streamlit run frontend/streamlit_app.py  # Terminal 2
```

---

## 📚 Documentação - Por Onde Começar?

### 1️⃣ Você é NOVO no sistema?
👉 Leia: **[README.md](README.md)**
- Visão geral completa
- Características do sistema
- Arquitetura

### 2️⃣ Quer USAR o sistema?
👉 Leia: **[docs/GUIA_USO.md](docs/GUIA_USO.md)**
- Tutorial passo a passo
- Como executar pipeline
- Como usar API e Frontend
- Troubleshooting

### 3️⃣ Quer ENTENDER os cálculos?
👉 Leia: **[docs/CALCULOS_RANKING.md](docs/CALCULOS_RANKING.md)**
- Metodologia detalhada
- Fórmulas e exemplos
- Interpretação dos scores

### 4️⃣ Usa DOCKER?
👉 Leia: **[DOCKER_QUICKSTART.md](DOCKER_QUICKSTART.md)**
- Comandos essenciais
- Referência rápida
- Troubleshooting Docker

### 5️⃣ Quer VER TUDO?
👉 Leia: **[docs/INDEX.md](docs/INDEX.md)**
- Índice completo da documentação
- Busca por caso de uso
- Links para todos os recursos

---

## 🗺️ Mapa da Documentação

```
📁 Documentação
│
├── 🏠 LEIA-ME-PRIMEIRO.md (você está aqui!)
│
├── 📖 Documentação Principal
│   ├── README.md                    → Visão geral
│   ├── docs/GUIA_USO.md            → Como usar
│   ├── docs/CALCULOS_RANKING.md    → Metodologia
│   └── docs/INDEX.md               → Índice completo
│
├── 🐳 Docker
│   ├── DOCKER_QUICKSTART.md        → Referência rápida
│   ├── APLICACAO_DOCKER_COMPLETA.md → Guia completo
│   ├── COMO_USAR_DOCKER.md         → Comandos
│   └── DOCKER_PIPELINE_RATE_LIMITING.md → Pipeline
│
├── 🔧 Técnica
│   ├── ESTRUTURA_DADOS_E_CALCULOS_RANKING.md → Schema
│   └── CHANGELOG.md                → Histórico de mudanças
│
└── 🌐 Online
    ├── http://localhost:8501       → Frontend
    ├── http://localhost:8000/docs  → API Swagger
    └── http://localhost:8000/redoc → API ReDoc
```

---

## 🎓 Trilhas de Aprendizado

### Trilha 1: Usuário Básico (30 min)
1. ✅ Leia este arquivo (5 min)
2. ✅ Execute [Início Rápido](#-início-rápido-5-minutos) (5 min)
3. ✅ Explore o Frontend em http://localhost:8501 (10 min)
4. ✅ Leia [README.md](README.md) - Seção "Uso" (10 min)

**Resultado**: Você sabe usar o sistema básico!

### Trilha 2: Usuário Avançado (1-2 horas)
1. ✅ Complete Trilha 1
2. ✅ Leia [docs/GUIA_USO.md](docs/GUIA_USO.md) completo (30 min)
3. ✅ Execute pipeline com ativos líquidos (20 min)
4. ✅ Explore a API em http://localhost:8000/docs (20 min)
5. ✅ Configure pesos customizados (10 min)

**Resultado**: Você domina todas as funcionalidades!

### Trilha 3: Desenvolvedor (3-4 horas)
1. ✅ Complete Trilha 2
2. ✅ Leia [docs/CALCULOS_RANKING.md](docs/CALCULOS_RANKING.md) (1 hora)
3. ✅ Leia [ESTRUTURA_DADOS_E_CALCULOS_RANKING.md](ESTRUTURA_DADOS_E_CALCULOS_RANKING.md) (30 min)
4. ✅ Explore o código em `app/` (1 hora)
5. ✅ Execute testes: `pytest tests/` (30 min)

**Resultado**: Você pode modificar e estender o sistema!

---

## 🔍 Busca Rápida

### Preciso de...

| O que você precisa | Onde encontrar |
|-------------------|----------------|
| Instalar e rodar | [Início Rápido](#-início-rápido-5-minutos) |
| Comandos Docker | [DOCKER_QUICKSTART.md](DOCKER_QUICKSTART.md) |
| Usar a API | [docs/GUIA_USO.md - Seção 4](docs/GUIA_USO.md#4-usar-a-api) |
| Executar pipeline | [docs/GUIA_USO.md - Seção 6](docs/GUIA_USO.md#6-executar-pipeline) |
| Entender cálculos | [docs/CALCULOS_RANKING.md](docs/CALCULOS_RANKING.md) |
| Resolver problemas | [docs/GUIA_USO.md - Seção 8](docs/GUIA_USO.md#8-troubleshooting) |
| Ver todas as docs | [docs/INDEX.md](docs/INDEX.md) |

---

## ❓ Perguntas Frequentes

### Como funciona o ranking?
O sistema combina 3 fatores (Momentum, Qualidade, Valor) com pesos configuráveis. Veja detalhes em [docs/CALCULOS_RANKING.md](docs/CALCULOS_RANKING.md).

### Preciso de API key?
Não! Usamos apenas Yahoo Finance que é gratuito.

### Quanto tempo leva o pipeline?
- 5 ativos: ~2 minutos
- 50 ativos: ~20 minutos
- 100 ativos: ~40 minutos

### Posso mudar os pesos dos fatores?
Sim! Edite `.env` e ajuste `MOMENTUM_WEIGHT`, `QUALITY_WEIGHT`, `VALUE_WEIGHT`.

### Como atualizar os dados?
Execute o pipeline novamente. Ele detecta automaticamente se precisa fazer update completo ou incremental.

### Onde ficam os dados?
No banco PostgreSQL (Docker) ou SQLite (local). Veja [ESTRUTURA_DADOS_E_CALCULOS_RANKING.md](ESTRUTURA_DADOS_E_CALCULOS_RANKING.md).

---

## 🆘 Precisa de Ajuda?

### Problemas Técnicos
1. Consulte [docs/GUIA_USO.md - Troubleshooting](docs/GUIA_USO.md#8-troubleshooting)
2. Veja logs: `docker-compose logs -f`
3. Abra uma issue no GitHub

### Dúvidas sobre Uso
1. Leia [docs/GUIA_USO.md](docs/GUIA_USO.md)
2. Consulte [docs/INDEX.md](docs/INDEX.md)
3. Veja exemplos na [API Swagger](http://localhost:8000/docs)

### Dúvidas sobre Metodologia
1. Leia [docs/CALCULOS_RANKING.md](docs/CALCULOS_RANKING.md)
2. Veja exemplos de cálculo na seção 10
3. Consulte as referências na seção 12

---

## 🎯 Próximos Passos

Agora que você leu este guia:

1. ✅ Execute o [Início Rápido](#-início-rápido-5-minutos)
2. ✅ Escolha sua [Trilha de Aprendizado](#-trilhas-de-aprendizado)
3. ✅ Explore a documentação conforme sua necessidade
4. ✅ Use o [docs/INDEX.md](docs/INDEX.md) como referência

---

## 📞 Contato

- **Issues**: https://github.com/edipo-dados/quant_stock_rank/issues
- **Documentação**: Você está nela! 😊

---

## ⚠️ Aviso Legal

Este sistema é apenas para fins educacionais e de pesquisa. Não constitui recomendação de investimento. Sempre consulte um profissional qualificado antes de tomar decisões de investimento.

---

**Boa sorte e bons investimentos! 🚀📈**

---

*Última atualização: 22 de Fevereiro de 2026*
