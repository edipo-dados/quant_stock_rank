# 📚 Índice Completo - Documentação de Deploy

## 🎯 Por Onde Começar?

### Nunca fez deploy antes?
→ Leia: **`DEPLOY_RESUMO.md`** (5 min)  
→ Depois: **`DECISION_TREE.md`** (3 min)  
→ Escolha: **`railway.md`** (deploy em 10 min)

### Já tem experiência?
→ Leia: **`DECISION_TREE.md`** (3 min)  
→ Escolha seu provedor em: **`../GUIA_DEPLOY.md`**  
→ Use: **`QUICK_REFERENCE.md`** para comandos

### Quer comparar opções?
→ Leia: **`../GUIA_DEPLOY.md`** (15 min)  
→ Compare: Tabelas de custo e features  
→ Decida: Baseado em suas necessidades

---

## 📁 Estrutura da Documentação

```
.
├── DEPLOY_RESUMO.md          ⭐ COMECE AQUI
├── GUIA_DEPLOY.md             📖 Guia completo (todas opções)
│
└── deploy/
    ├── INDEX.md               📚 Este arquivo
    ├── DECISION_TREE.md       🌳 Árvore de decisão
    ├── QUICK_REFERENCE.md     ⚡ Comandos rápidos
    ├── README.md              📝 Visão geral dos scripts
    │
    ├── railway.md             🚂 Guia Railway (mais fácil)
    │
    ├── vps-setup.sh           🔧 Setup automático VPS
    ├── nginx.conf             🌐 Config Nginx
    ├── backup-db.sh           💾 Backup automático
    └── restore-db.sh          🔄 Restauração
```

---

## 📖 Guias por Tipo

### Guias de Decisão
1. **`DEPLOY_RESUMO.md`** - Resumo executivo com recomendações
2. **`DECISION_TREE.md`** - Árvore de decisão interativa
3. **`../GUIA_DEPLOY.md`** - Comparação detalhada de todas opções

### Guias de Implementação
1. **`railway.md`** - Deploy no Railway (PaaS mais fácil)
2. **`../GUIA_DEPLOY.md`** - Seções específicas para cada provedor:
   - Railway
   - Render
   - Fly.io
   - AWS ECS
   - DigitalOcean
   - VPS Manual

### Guias de Manutenção
1. **`QUICK_REFERENCE.md`** - Comandos essenciais do dia-a-dia
2. **`README.md`** - Documentação dos scripts de automação

---

## 🎯 Fluxo de Leitura Recomendado

### Para Iniciantes

```
1. DEPLOY_RESUMO.md (5 min)
   ↓
2. DECISION_TREE.md (3 min)
   ↓
3. railway.md (10 min)
   ↓
4. QUICK_REFERENCE.md (bookmark para depois)
```

**Tempo total:** 20 minutos + deploy

---

### Para Intermediários

```
1. DECISION_TREE.md (3 min)
   ↓
2. GUIA_DEPLOY.md - Seção específica (15 min)
   ↓
3. Executar scripts de setup
   ↓
4. QUICK_REFERENCE.md (referência)
```

**Tempo total:** 20 minutos + setup (1-2 horas)

---

### Para Avançados

```
1. GUIA_DEPLOY.md - Comparação rápida (5 min)
   ↓
2. Escolher provedor
   ↓
3. Adaptar scripts conforme necessário
   ↓
4. QUICK_REFERENCE.md (comandos úteis)
```

**Tempo total:** Direto ao ponto

---

## 📊 Documentos por Objetivo

### Quero Decidir Onde Fazer Deploy
1. `DEPLOY_RESUMO.md` - Tabela comparativa rápida
2. `DECISION_TREE.md` - Perguntas e respostas
3. `GUIA_DEPLOY.md` - Análise detalhada

### Quero Fazer Deploy Agora
1. `railway.md` - Mais rápido (10 min)
2. `GUIA_DEPLOY.md` → Seção VPS - Controle total (1-2h)
3. `GUIA_DEPLOY.md` → Seção AWS - Enterprise (2-4h)

### Quero Manter a Aplicação
1. `QUICK_REFERENCE.md` - Comandos diários
2. `README.md` - Scripts de backup/restore
3. `GUIA_DEPLOY.md` → Seção Monitoramento

### Quero Resolver Problemas
1. `QUICK_REFERENCE.md` → Seção Troubleshooting
2. `GUIA_DEPLOY.md` → Seção específica do provedor
3. Logs: `docker compose logs -f`

---

## 🔍 Busca Rápida

### Por Provedor

| Provedor | Documento | Seção |
|----------|-----------|-------|
| Railway | `railway.md` | Guia completo |
| Render | `GUIA_DEPLOY.md` | Opção 2 |
| Fly.io | `GUIA_DEPLOY.md` | Opção 3 |
| AWS | `GUIA_DEPLOY.md` | Opção 4 |
| DigitalOcean | `GUIA_DEPLOY.md` | Opção 5 |
| VPS | `GUIA_DEPLOY.md` | Opção 6 |

### Por Tarefa

| Tarefa | Documento | Comando/Seção |
|--------|-----------|---------------|
| Backup | `backup-db.sh` | `./deploy/backup-db.sh` |
| Restore | `restore-db.sh` | `./deploy/restore-db.sh` |
| Setup VPS | `vps-setup.sh` | `sudo bash vps-setup.sh` |
| Config Nginx | `nginx.conf` | Copiar para `/etc/nginx/` |
| Ver logs | `QUICK_REFERENCE.md` | Seção Monitoramento |
| Health check | `QUICK_REFERENCE.md` | Seção Health Checks |

### Por Problema

| Problema | Documento | Seção |
|----------|-----------|-------|
| Container não inicia | `QUICK_REFERENCE.md` | Troubleshooting |
| Banco não conecta | `QUICK_REFERENCE.md` | Banco de Dados |
| Nginx erro | `QUICK_REFERENCE.md` | Nginx |
| SSL não funciona | `QUICK_REFERENCE.md` | SSL/HTTPS |
| Porta em uso | `QUICK_REFERENCE.md` | Troubleshooting |
| Disco cheio | `QUICK_REFERENCE.md` | Troubleshooting |

---

## 📝 Checklists

### Checklist Pré-Deploy
→ `DEPLOY_RESUMO.md` → Seção "Checklist Pré-Deploy"

### Checklist Pós-Deploy
→ `DEPLOY_RESUMO.md` → Seção "Checklist Pós-Deploy"

### Checklist de Segurança
→ `README.md` → Seção "Segurança"

### Checklist Diário
→ `QUICK_REFERENCE.md` → Seção "Checklist Diário"

---

## 🛠️ Scripts Disponíveis

### Automação
- **`vps-setup.sh`** - Setup completo de VPS Ubuntu
  - Instala Docker, Nginx, Certbot
  - Configura firewall e fail2ban
  - Cria usuário deploy
  - Tempo: ~5 minutos

### Backup/Restore
- **`backup-db.sh`** - Backup automático do PostgreSQL
  - Cria backup comprimido
  - Remove backups antigos (30 dias)
  - Pode ser agendado via cron

- **`restore-db.sh`** - Restauração do banco
  - Restaura de backup .sql ou .sql.gz
  - Para aplicação durante restore
  - Verifica saúde após restore

### Configuração
- **`nginx.conf`** - Template Nginx pronto
  - Frontend (Streamlit)
  - Backend (FastAPI)
  - SSL/HTTPS (comentado)
  - WebSocket para Streamlit

---

## 💡 Dicas de Uso

### Primeira Vez
1. Leia `DEPLOY_RESUMO.md` primeiro
2. Use `DECISION_TREE.md` para escolher
3. Siga o guia específico do provedor
4. Salve `QUICK_REFERENCE.md` como bookmark

### Dia a Dia
1. Use `QUICK_REFERENCE.md` para comandos
2. Configure backups automáticos
3. Monitore logs regularmente
4. Mantenha documentação atualizada

### Troubleshooting
1. Verifique logs primeiro
2. Consulte `QUICK_REFERENCE.md`
3. Procure no guia do provedor
4. Abra issue no GitHub se necessário

---

## 🎓 Níveis de Conhecimento

### Iniciante
**Leia:**
- `DEPLOY_RESUMO.md`
- `DECISION_TREE.md`
- `railway.md`

**Pule:**
- Scripts bash (use Railway)
- Configuração manual de servidor
- AWS/Kubernetes

### Intermediário
**Leia:**
- `DECISION_TREE.md`
- `GUIA_DEPLOY.md` (seções relevantes)
- `QUICK_REFERENCE.md`

**Use:**
- Scripts de setup
- Docker Compose
- Nginx básico

### Avançado
**Leia:**
- `GUIA_DEPLOY.md` (comparação)
- Documentação do provedor escolhido

**Customize:**
- Scripts conforme necessário
- Infraestrutura como código
- CI/CD pipelines

---

## 📞 Suporte

### Documentação
- Todos os guias estão na pasta `deploy/`
- Use o índice acima para navegar
- Comandos rápidos em `QUICK_REFERENCE.md`

### Comunidade
- GitHub Issues do projeto
- Discord/Slack do provedor escolhido
- Stack Overflow para problemas técnicos

### Profissional
- Consultoria DevOps
- Suporte do provedor (planos pagos)
- Managed services

---

## 🔄 Atualizações

Este índice é atualizado quando:
- Novos guias são adicionados
- Provedores mudam significativamente
- Feedback dos usuários

**Última atualização:** 2026-02-20

---

## ✅ Próximos Passos

1. **Escolha seu caminho:**
   - Iniciante → `DEPLOY_RESUMO.md`
   - Experiente → `DECISION_TREE.md`
   - Urgente → `railway.md`

2. **Siga o guia escolhido**

3. **Salve `QUICK_REFERENCE.md` como bookmark**

4. **Configure monitoramento e backups**

5. **Documente suas customizações**

---

**Boa sorte com o deploy! 🚀**

*Dúvidas? Comece por `DEPLOY_RESUMO.md`*
