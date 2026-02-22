# 🚀 Deploy - Resumo Executivo

## Qual opção escolher?

### 🎯 Recomendação por Caso de Uso

| Seu Caso | Recomendação | Custo/mês | Tempo Setup |
|----------|--------------|-----------|-------------|
| **Testar/MVP rápido** | Railway | $5-15 | 10 min |
| **Projeto pessoal** | Fly.io ou Railway | $0-20 | 15 min |
| **Startup pequena** | Render ou DigitalOcean | $12-30 | 30 min |
| **Produção séria** | DigitalOcean ou AWS | $30-100 | 2-4 horas |
| **Máximo controle** | VPS (Contabo/Hetzner) | €4-10 | 1-2 horas |

---

## ⚡ Deploy em 10 Minutos (Railway)

**Melhor para:** Começar rápido, testar, MVP

```bash
1. Acesse: https://railway.app
2. Login com GitHub
3. New Project → Deploy from GitHub
4. Adicione PostgreSQL
5. Configure variáveis de ambiente
6. Deploy automático!
```

**Custo:** ~$10/mês  
**Guia completo:** `deploy/railway.md`

---

## 💪 Deploy Profissional (VPS)

**Melhor para:** Controle total, custo baixo

```bash
# 1. Provisionar VPS (Contabo, Hetzner, DigitalOcean)
# 2. Executar setup automático
wget https://raw.githubusercontent.com/seu-usuario/seu-repo/main/deploy/vps-setup.sh
sudo bash vps-setup.sh

# 3. Clonar e configurar
su - deploy
git clone https://github.com/seu-usuario/seu-repo.git
cd seu-repo
cp .env.example .env
nano .env

# 4. Deploy
docker compose up -d --build

# 5. Configurar Nginx + SSL
sudo cp deploy/nginx.conf /etc/nginx/sites-available/quant-ranker
sudo ln -s /etc/nginx/sites-available/quant-ranker /etc/nginx/sites-enabled/
sudo certbot --nginx -d seu-dominio.com
```

**Custo:** €4-10/mês  
**Guia completo:** `GUIA_DEPLOY.md`

---

## 📋 Checklist Pré-Deploy

### Obrigatório
- [ ] Repositório Git configurado
- [ ] Arquivo `.env` com variáveis corretas
- [ ] Chave API do Yahoo Finance (se necessário)
- [ ] Domínio registrado (opcional mas recomendado)

### Recomendado
- [ ] Conta no provedor escolhido
- [ ] Cartão de crédito para billing
- [ ] Email para notificações
- [ ] Plano de backup definido

---

## 🔧 Configuração Mínima (.env)

```bash
# Database
DATABASE_URL=postgresql://user:pass@host:5432/db

# API Keys
FMP_API_KEY=sua_chave_aqui

# Scoring (opcional, tem defaults)
MOMENTUM_WEIGHT=0.4
QUALITY_WEIGHT=0.3
VALUE_WEIGHT=0.3

# Ports (opcional)
API_PORT=8000
FRONTEND_PORT=8501
```

---

## 📊 Comparação de Custos

### Mensal

| Provedor | Básico | Recomendado | Enterprise |
|----------|--------|-------------|------------|
| Railway | $5 | $10-15 | $20-30 |
| Render | $7 | $15-25 | $40-60 |
| Fly.io | $0 | $10-20 | $30-50 |
| DigitalOcean | $12 | $24-36 | $60-100 |
| AWS ECS | $30 | $50-80 | $100-200 |
| VPS (Contabo) | €4 | €8 | €16 |

### Anual (com desconto)

| Provedor | Básico | Recomendado |
|----------|--------|-------------|
| Railway | $60 | $120-180 |
| VPS | €48 | €96 |
| DigitalOcean | $144 | $288-432 |

**Economia:** VPS pode economizar 50-70% vs PaaS

---

## 🎯 Decisão Rápida

### Escolha Railway se:
- ✅ Quer começar AGORA
- ✅ Não quer lidar com infraestrutura
- ✅ Orçamento até $20/mês
- ✅ Projeto pequeno/médio

### Escolha VPS se:
- ✅ Quer controle total
- ✅ Sabe usar Linux/Docker
- ✅ Quer custo mínimo
- ✅ Precisa customização

### Escolha AWS/DigitalOcean se:
- ✅ Projeto em produção
- ✅ Precisa escalar
- ✅ Tem orçamento $50+/mês
- ✅ Quer serviços gerenciados

---

## 🚦 Próximos Passos

### 1. Escolher Provedor
Baseado na tabela acima

### 2. Seguir Guia Específico
- Railway: `deploy/railway.md`
- VPS: `GUIA_DEPLOY.md` → Seção VPS
- Outros: `GUIA_DEPLOY.md` → Seção específica

### 3. Configurar Monitoramento
- UptimeRobot (grátis)
- Sentry (grátis até 5k eventos)

### 4. Configurar Backups
```bash
# Automático via cron
crontab -e
0 2 * * * /path/to/deploy/backup-db.sh
```

### 5. Testar Aplicação
```bash
# Backend
curl https://api.seu-dominio.com/health

# Frontend
# Abrir no navegador
https://seu-dominio.com
```

---

## 📞 Precisa de Ajuda?

### Documentação
- **Guia completo:** `GUIA_DEPLOY.md`
- **Railway:** `deploy/railway.md`
- **Scripts:** `deploy/README.md`

### Suporte por Provedor
- **Railway:** https://discord.gg/railway
- **Render:** https://render.com/docs
- **Fly.io:** https://community.fly.io
- **DigitalOcean:** https://www.digitalocean.com/community

### Troubleshooting Comum
```bash
# Container não inicia
docker compose logs <service>

# Banco não conecta
docker compose exec postgres pg_isready

# Nginx erro
sudo nginx -t
sudo tail -f /var/log/nginx/error.log
```

---

## 💡 Dicas Finais

1. **Comece simples:** Railway para testar, depois migre se necessário
2. **Sempre faça backup:** Configure desde o dia 1
3. **Use HTTPS:** Certbot é grátis e fácil
4. **Monitore:** UptimeRobot é grátis e essencial
5. **Documente:** Anote senhas, URLs, configurações
6. **Teste antes:** Sempre teste em staging primeiro
7. **Automatize:** Use scripts para tarefas repetitivas
8. **Versione:** Use tags Git para releases

---

## ✅ Checklist Pós-Deploy

- [ ] Aplicação acessível via URL
- [ ] Backend respondendo (/health)
- [ ] Frontend carregando
- [ ] Banco de dados conectado
- [ ] Pipeline executado com sucesso
- [ ] Dados visíveis no frontend
- [ ] SSL/HTTPS funcionando
- [ ] Monitoramento configurado
- [ ] Backups automáticos ativos
- [ ] Logs sendo coletados
- [ ] Documentação atualizada
- [ ] Credenciais salvas em local seguro

---

**Pronto para começar?** Escolha sua opção e siga o guia correspondente!

**Tempo estimado total:**
- Railway: 10-15 minutos
- VPS: 1-2 horas
- AWS: 2-4 horas

**Boa sorte com o deploy! 🚀**
