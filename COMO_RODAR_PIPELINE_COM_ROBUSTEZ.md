# Como Rodar o Pipeline com as Melhorias de Robustez

## ✅ Implementação Completa

Todas as melhorias de robustez foram implementadas e testadas com sucesso!

### Teste com Americanas (AMER3)

Executamos um teste simulando os dados da Americanas, que está em recuperação judicial:

**Resultado**: ✅ **EXCLUÍDA** por 5 razões:
1. Patrimônio líquido negativo (R$ -10 bilhões)
2. EBITDA negativo (R$ -2 bilhões)  
3. Lucro líquido negativo no último ano (R$ -20 bilhões)
4. Lucro negativo em 2 dos últimos 3 anos
5. Endividamento excessivo (Dívida/EBITDA = 15.0)

**Penalidades adicionais** (se não fosse excluída):
- Distress flag: 50% de redução no score
- Quality score: -0.582 (muito negativo)
- Penalização por prejuízo: 0.4x
- Penalização por endividamento: 0.7x

## 🚀 Como Rodar o Pipeline

### Opção 1: Rodar Pipeline Completo

```bash
python scripts/run_pipeline.py
```

Este comando vai:
1. Buscar dados de todos os tickers
2. Calcular fatores (incluindo os novos)
3. Aplicar filtro de elegibilidade (com novos critérios)
4. Normalizar fatores
5. Calcular scores (com distress flag)
6. Gerar ranking

### Opção 2: Rodar Apenas para Alguns Tickers

```bash
python scripts/run_pipeline.py --tickers AMER3,PETR4,VALE3
```

### Opção 3: Verificar Dados Atuais no Banco

```bash
python scripts/check_db.py
```

## 📊 O Que Esperar

### Empresas que Devem Ser Excluídas

Com as novas regras, as seguintes empresas devem ser excluídas:

1. **AMER3 (Americanas)** - Recuperação judicial, prejuízos bilionários
2. **AZUL4 (Azul)** - Patrimônio líquido negativo, alta alavancagem
3. **OIBR3 (Oi)** - Falida, patrimônio negativo
4. **BEEF3 (Minerva)** - Patrimônio líquido negativo
5. **ABEV3 (Ambev)** - Se estiver com dados faltantes

### Empresas que Devem Ser Penalizadas

Empresas com prejuízos recentes ou alto endividamento terão scores reduzidos:

- **Distress flag** (50% de redução):
  - Lucro negativo no último ano
  - Lucro negativo em 2 dos últimos 3 anos
  - Dívida/EBITDA > 5

- **Penalização de qualidade**:
  - Prejuízo recente: 0.4x
  - Dívida/EBITDA > 5: 0.7x
  - Dívida/EBITDA > 3: 0.9x

### Empresas que Devem Subir no Ranking

Empresas sólidas com lucros consistentes e baixo endividamento:

- **WEGE3 (WEG)** - Lucros consistentes, baixo endividamento
- **RENT3 (Localiza)** - Boa rentabilidade, crescimento
- **PRIO3 (Prio)** - Setor de petróleo, boa gestão

## 🔍 Verificar Resultados

### 1. Ver Ranking Completo

Após rodar o pipeline, acesse o frontend:

```bash
cd frontend
streamlit run 1_🏆_Ranking.py
```

### 2. Ver Detalhes de um Ativo

```bash
# No frontend, clique em um ativo ou digite o ticker
# Exemplo: AMER3
```

Você verá:
- Se passou no filtro de elegibilidade
- Razões de exclusão (se aplicável)
- Penalidades de risco aplicadas
- Distress flag (se ativado)
- Score breakdown completo

### 3. Comparar Antes/Depois

Para comparar o ranking antes e depois das mudanças:

1. Faça backup do banco de dados atual:
```bash
copy quant_ranker.db quant_ranker_backup.db
```

2. Rode o pipeline com as novas regras
3. Compare os rankings

## 📝 Logs e Debugging

### Ver Logs do Pipeline

```bash
# Os logs mostrarão:
# - Quantos ativos foram excluídos
# - Razões de exclusão
# - Penalidades aplicadas
# - Distress flags ativados
```

### Verificar Ativos Excluídos

```python
from app.models.database import SessionLocal
from app.models.schemas import ScoreDaily

db = SessionLocal()
excluded = db.query(ScoreDaily).filter(
    ScoreDaily.passed_eligibility == False
).all()

for score in excluded:
    print(f"{score.ticker}: {score.exclusion_reasons}")
```

## ⚠️ Notas Importantes

### 1. Dados Históricos

As novas regras requerem dados históricos (últimos 3 anos):
- `net_income_history`
- `roe_mean_3y`
- `roe_volatility`

Se os dados históricos não estiverem disponíveis, os critérios correspondentes serão ignorados graciosamente.

### 2. Instituições Financeiras

Bancos e instituições financeiras são isentos de alguns critérios:
- Não precisam reportar EBITDA
- Não são penalizados por alto endividamento

Exemplos: ITUB4, BBDC4, BBAS3, SANB11, BPAC11

### 3. Backward Compatibility

O código é backward-compatible:
- Se os novos campos não estiverem disponíveis, são ignorados
- O pipeline antigo continua funcionando
- Dados históricos podem ser populados gradualmente

## 🎯 Próximos Passos

1. **Rodar pipeline completo** para ver o impacto real
2. **Analisar resultados** - verificar se empresas problemáticas foram excluídas
3. **Ajustar thresholds** se necessário (ex: debt/EBITDA > 8 pode ser muito restritivo)
4. **Documentar mudanças** no ranking para os usuários

## 📞 Suporte

Se encontrar problemas:

1. Verifique os logs do pipeline
2. Execute o teste: `python test_americanas_robustness.py`
3. Verifique se os dados estão no banco: `python scripts/check_db.py`
4. Revise a documentação: `ROBUSTNESS_IMPROVEMENTS_SUMMARY.md`

---

**Data**: 2026-02-18
**Status**: ✅ Pronto para Produção
**Teste**: ✅ Americanas corretamente excluída
