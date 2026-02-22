# 🚀 Início Rápido - Quant Stock Ranker

## Scripts Disponíveis

### 1. `start_all.bat` - Inicialização Completa
Executa todo o processo de inicialização:
- ✅ Verifica/cria ambiente virtual
- ✅ Inicializa banco de dados
- ✅ Roda pipeline completo (ativos líquidos B3)
- ✅ Inicia backend (FastAPI)
- ✅ Inicia frontend (Streamlit)
- ✅ Abre navegador automaticamente

**Uso:**
```bash
start_all.bat
```

**Quando usar:** Primeira vez ou quando quiser processar dados novos.

---

### 2. `start_dev.bat` - Modo Desenvolvimento
Inicia apenas backend e frontend (sem rodar pipeline):
- ✅ Inicia backend (FastAPI)
- ✅ Inicia frontend (Streamlit)
- ✅ Abre navegador automaticamente

**Uso:**
```bash
start_dev.bat
```

**Quando usar:** Desenvolvimento rápido com dados já existentes no banco.

---

### 3. `stop_all.bat` - Parar Aplicação
Para todos os processos:
- ✅ Para backend (porta 8000)
- ✅ Para frontend (porta 8501)

**Uso:**
```bash
stop_all.bat
```

---

## URLs da Aplicação

Após iniciar, acesse:

- **Frontend (Interface):** http://localhost:8501
- **Backend (API):** http://localhost:8000
- **Documentação API:** http://localhost:8000/docs
- **Health Check:** http://localhost:8000/health

---

## Fluxo Recomendado

### Primeira Vez
```bash
# 1. Instalar dependências (se ainda não fez)
pip install -r requirements.txt

# 2. Configurar .env (copiar de .env.example)
copy .env.example .env

# 3. Iniciar tudo
start_all.bat
```

### Desenvolvimento Diário
```bash
# Iniciar apenas backend e frontend
start_dev.bat

# Quando terminar
stop_all.bat
```

### Atualizar Dados
```bash
# Rodar pipeline manualmente
python scripts/run_pipeline.py --mode production

# Ou rodar com ativos específicos
python scripts/run_pipeline.py --mode test --tickers PETR4,VALE3,ITUB4 --limit 10
```

---

## Troubleshooting

### Porta já em uso
Se receber erro de porta já em uso:
```bash
stop_all.bat
```

### Banco de dados vazio
Se não houver dados no banco:
```bash
python scripts/run_pipeline.py --mode production
```

### Erro de importação
Reinstalar dependências:
```bash
pip install -r requirements.txt --force-reinstall
```

---

## Estrutura de Dados

Após rodar o pipeline, o banco terá:
- **asset_info:** Informações dos ativos (setor, nome, etc)
- **raw_prices_daily:** Preços históricos
- **raw_fundamentals:** Dados fundamentalistas
- **features_daily:** Fatores de momentum calculados
- **features_monthly:** Fatores fundamentalistas calculados
- **scores_daily:** Scores finais e ranking

---

## Modos do Pipeline

### Modo Test
Processa poucos ativos para teste rápido:
```bash
python scripts/run_pipeline.py --mode test --tickers PETR4,VALE3,ITUB4 --limit 5
```

### Modo Production
Processa todos os ativos líquidos da B3:
```bash
python scripts/run_pipeline.py --mode production
```

---

## Próximos Passos

1. ✅ Inicie a aplicação com `start_all.bat`
2. ✅ Acesse http://localhost:8501
3. ✅ Explore o ranking de ativos
4. ✅ Veja detalhes de ativos específicos
5. ✅ Consulte a API em http://localhost:8000/docs

---

## Suporte

Para mais detalhes, consulte:
- `README.md` - Documentação completa
- `ESTRUTURA_DADOS_E_CALCULOS_RANKING.md` - Como funciona o ranking
- `COMO_RODAR_PIPELINE_COM_ROBUSTEZ.md` - Detalhes do pipeline
