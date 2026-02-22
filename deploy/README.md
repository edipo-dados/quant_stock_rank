# 📦 Scripts e Documentação de Deploy

Esta pasta contém toda a documentação e scripts para deploy da aplicação em diferentes plataformas.

---

## 🚀 Deploy no Render (Recomendado) ⭐

### Documentação Completa

| Arquivo | Descrição | Quando Usar |
|---------|-----------|-------------|
| **RENDER_INDEX.md** | 📚 Índice completo | Navegação |
| **RENDER_COMPLETO.md** | 📖 Guia completo passo a passo | Primeira vez |
| **RENDER_QUICK_START.md** | ⚡ Guia rápido (10 min) | Deploy rápido |
| **RENDER_CHECKLIST.md** | ✅ Checklist visual | Acompanhamento |
| **RENDER_COMANDOS.md** | 🛠️ Comandos úteis | Manutenção |
| **RENDER_DICAS.md** | 💡 Melhores práticas | Otimização |

### Como Começar com Render

**Primeira vez?**
```
1. Leia: ../DEPLOY_RENDER_RESUMO.md (na raiz)
2. Siga: RENDER_COMPLETO.md
3. Use: RENDER_CHECKLIST.md durante o deploy
```

**Já conhece Render?**
```
1. Siga: RENDER_QUICK_START.md
2. Consulte: RENDER_COMANDOS.md conforme necessário
```

**Custo:** $21/mês (Starter) ou $0 (Free Tier com limitações)

---

## 🌐 Outras Opções de Deploy

### Railway
- **Arquivo:** `railway.md`
- **Descrição:** Deploy no Railway (alternativa ao Render)
- **Custo:** $5-15/mês
- **Complexidade:** ⭐ Baixa

### VPS Manual
- **Arquivo:** `vps-setup.sh`
- **Descrição:** Setup automático em VPS
- **Custo:** $5-20/mês
- **Complexidade:** ⭐⭐⭐ Alta
- **Requer:** Conhecimento técnico

### Nginx
- **Arquivo:** `nginx.conf`
- **Descrição:** Configuração do Nginx para VPS
- **Uso:** Reverse proxy

---

## 📁 Arquivos

### Guias de Deploy

- **`railway.md`** - Guia completo para deploy no Railway (mais fácil)
- **`../GUIA_DEPLOY.md`** - Guia geral com todas as opções de deploy

### Scripts de Automação

- **`vps-setup.sh`** - Setup automático de VPS Ubuntu
- **`backup-db.sh`** - Backup automático do banco de dados
- **`restore-db.sh`** - Restauração do banco de dados

### Configurações

- **`nginx.conf`** - Configuração do Nginx como reverse proxy

---

## 🚀 Quick Start

### Deploy Rápido (Railway)

```bash
# 1. Siga o guia
cat deploy/railway.md

# 2. Acesse Railway
# https://railway.app

# 3. Deploy em 5 minutos!
```

### Deploy em VPS

```bash
# 1. Conectar ao VPS
ssh root@seu-ip

# 2. Baixar e executar setup
wget https://raw.githubusercontent.com/seu-usuario/seu-repo/main/deploy/vps-setup.sh
chmod +x vps-setup.sh
sudo ./vps-setup.sh

# 3. Clonar repositório
su - deploy
git clone https://github.com/seu-usuario/seu-repo.git
cd seu-repo

# 4. Configurar ambiente
cp .env.example .env
nano .env

# 5. Iniciar aplicação
docker compose up -d --build

# 6. Configurar Nginx
sudo cp deploy/nginx.conf /etc/nginx/sites-available/quant-ranker
sudo ln -s /etc/nginx/sites-available/quant-ranker /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx

# 7. Configurar SSL
sudo certbot --nginx -d seu-dominio.com -d api.seu-dominio.com
```

---

## 🔧 Scripts de Manutenção

### Backup do Banco de Dados

```bash
# Backup manual
./deploy/backup-db.sh

# Configurar backup automático (cron)
crontab -e

# Adicionar linha (backup diário às 2h)
0 2 * * * /home/deploy/seu-repo/deploy/backup-db.sh >> /home/deploy/logs/backup.log 2>&1
```

### Restaurar Banco de Dados

```bash
# Listar backups disponíveis
ls -lh /home/deploy/backups/

# Restaurar backup específico
./deploy/restore-db.sh /home/deploy/backups/quant_ranker_backup_20260220_020000.sql.gz
```

---

## 📊 Monitoramento

### Verificar Status

```bash
# Status dos containers
docker compose ps

# Logs em tempo real
docker compose logs -f

# Logs específicos
docker compose logs -f backend
docker compose logs -f frontend
docker compose logs -f postgres

# Health checks
curl http://localhost:8000/health
curl http://localhost:8501/_stcore/health
```

### Métricas do Sistema

```bash
# Uso de recursos
docker stats

# Espaço em disco
df -h

# Memória
free -h

# Processos
htop
```

---

## 🔄 Atualizações

### Atualizar Aplicação

```bash
# 1. Fazer backup
./deploy/backup-db.sh

# 2. Baixar atualizações
git pull origin main

# 3. Rebuild e restart
docker compose down
docker compose up -d --build

# 4. Verificar logs
docker compose logs -f
```

### Rollback

```bash
# 1. Voltar para versão anterior
git checkout <commit-hash>

# 2. Rebuild
docker compose down
docker compose up -d --build

# 3. Restaurar banco se necessário
./deploy/restore-db.sh /home/deploy/backups/backup_anterior.sql.gz
```

---

## 🛡️ Segurança

### Checklist de Segurança

- [ ] Firewall configurado (UFW)
- [ ] Fail2ban ativo
- [ ] SSL/HTTPS configurado
- [ ] Senhas fortes no .env
- [ ] Backups automáticos configurados
- [ ] Monitoramento ativo
- [ ] Logs sendo coletados
- [ ] Atualizações de segurança automáticas

### Configurar Atualizações Automáticas

```bash
# Instalar unattended-upgrades
sudo apt install unattended-upgrades

# Configurar
sudo dpkg-reconfigure -plow unattended-upgrades
```

---

## 📞 Troubleshooting

### Container não inicia

```bash
# Ver logs detalhados
docker compose logs <service-name>

# Verificar configuração
docker compose config

# Rebuild forçado
docker compose down
docker compose build --no-cache
docker compose up -d
```

### Banco de dados não conecta

```bash
# Verificar se PostgreSQL está rodando
docker compose ps postgres

# Testar conexão
docker compose exec postgres pg_isready -U quant_user

# Ver logs do PostgreSQL
docker compose logs postgres
```

### Nginx não funciona

```bash
# Testar configuração
sudo nginx -t

# Ver logs
sudo tail -f /var/log/nginx/error.log

# Restart
sudo systemctl restart nginx
```

### SSL não funciona

```bash
# Renovar certificados
sudo certbot renew

# Testar renovação
sudo certbot renew --dry-run

# Ver logs
sudo tail -f /var/log/letsencrypt/letsencrypt.log
```

---

## 📚 Recursos Adicionais

- [Documentação Docker](https://docs.docker.com/)
- [Documentação Nginx](https://nginx.org/en/docs/)
- [Let's Encrypt](https://letsencrypt.org/)
- [Railway Docs](https://docs.railway.app/)
- [DigitalOcean Tutorials](https://www.digitalocean.com/community/tutorials)

---

## 💡 Dicas

1. **Sempre faça backup antes de atualizações**
2. **Monitore logs regularmente**
3. **Configure alertas de uptime**
4. **Documente mudanças de configuração**
5. **Teste em ambiente de staging primeiro**
6. **Mantenha senhas em gerenciador seguro**
7. **Configure renovação automática de SSL**
8. **Use tags de versão no Git**

---

## 🆘 Suporte

Se precisar de ajuda:

1. Verifique os logs primeiro
2. Consulte a documentação
3. Procure no GitHub Issues
4. Abra uma issue detalhada

---

**Última atualização:** 2026-02-20
