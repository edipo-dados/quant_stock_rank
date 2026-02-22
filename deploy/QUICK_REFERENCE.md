# ⚡ Referência Rápida - Comandos Essenciais

## 🚀 Deploy

### Railway (Mais Fácil)
```bash
# 1. Acesse https://railway.app
# 2. Login com GitHub
# 3. New Project → Deploy from GitHub
# 4. Add PostgreSQL
# 5. Configure variáveis
# 6. Deploy automático!
```

### VPS (Controle Total)
```bash
# Setup inicial
wget https://raw.githubusercontent.com/seu-usuario/seu-repo/main/deploy/vps-setup.sh
sudo bash vps-setup.sh

# Deploy
su - deploy
git clone https://github.com/seu-usuario/seu-repo.git
cd seu-repo
cp .env.example .env
nano .env
docker compose up -d --build
```

---

## 🔧 Comandos Docker

### Gerenciamento
```bash
# Iniciar tudo
docker compose up -d

# Parar tudo
docker compose down

# Rebuild e restart
docker compose up -d --build

# Ver status
docker compose ps

# Ver logs
docker compose logs -f
docker compose logs -f backend
docker compose logs -f frontend
docker compose logs -f postgres
```

### Manutenção
```bash
# Entrar no container
docker compose exec backend bash
docker compose exec postgres bash

# Executar comando
docker compose exec backend python scripts/run_pipeline.py --mode liquid

# Limpar volumes
docker compose down -v

# Limpar tudo
docker system prune -a
```

---

## 🗄️ Banco de Dados

### Backup
```bash
# Manual
./deploy/backup-db.sh

# Automático (cron)
crontab -e
# Adicionar: 0 2 * * * /path/to/deploy/backup-db.sh
```

### Restauração
```bash
# Listar backups
ls -lh /home/deploy/backups/

# Restaurar
./deploy/restore-db.sh /path/to/backup.sql.gz
```

### Acesso Direto
```bash
# Via Docker
docker compose exec postgres psql -U quant_user quant_ranker

# Comandos úteis no psql
\dt              # Listar tabelas
\d+ table_name   # Descrever tabela
SELECT COUNT(*) FROM scores_daily;
\q               # Sair
```

---

## 🔍 Monitoramento

### Health Checks
```bash
# Backend
curl http://localhost:8000/health

# Frontend
curl http://localhost:8501/_stcore/health

# Database
docker compose exec postgres pg_isready -U quant_user
```

### Logs
```bash
# Tempo real
docker compose logs -f

# Últimas 100 linhas
docker compose logs --tail=100

# Logs específicos
docker compose logs backend --tail=50

# Logs do sistema
sudo tail -f /var/log/nginx/error.log
sudo tail -f /var/log/syslog
```

### Recursos
```bash
# Uso de containers
docker stats

# Espaço em disco
df -h

# Memória
free -h

# Processos
htop
```

---

## 🌐 Nginx

### Comandos
```bash
# Testar configuração
sudo nginx -t

# Reload (sem downtime)
sudo nginx -s reload

# Restart
sudo systemctl restart nginx

# Status
sudo systemctl status nginx

# Logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

### Configuração
```bash
# Editar config
sudo nano /etc/nginx/sites-available/quant-ranker

# Ativar site
sudo ln -s /etc/nginx/sites-available/quant-ranker /etc/nginx/sites-enabled/

# Desativar site
sudo rm /etc/nginx/sites-enabled/quant-ranker
```

---

## 🔒 SSL/HTTPS

### Certbot
```bash
# Obter certificado
sudo certbot --nginx -d seu-dominio.com -d api.seu-dominio.com

# Renovar manualmente
sudo certbot renew

# Testar renovação
sudo certbot renew --dry-run

# Listar certificados
sudo certbot certificates

# Logs
sudo tail -f /var/log/letsencrypt/letsencrypt.log
```

---

## 🔄 Atualizações

### Aplicação
```bash
# 1. Backup
./deploy/backup-db.sh

# 2. Atualizar código
git pull origin main

# 3. Rebuild
docker compose down
docker compose up -d --build

# 4. Verificar
docker compose logs -f
```

### Sistema
```bash
# Atualizar pacotes
sudo apt update && sudo apt upgrade -y

# Atualizar Docker
curl -fsSL https://get.docker.com | sh

# Limpar pacotes antigos
sudo apt autoremove -y
```

---

## 🐛 Troubleshooting

### Container não inicia
```bash
# Ver erro
docker compose logs <service>

# Rebuild forçado
docker compose down
docker compose build --no-cache
docker compose up -d

# Verificar config
docker compose config
```

### Banco não conecta
```bash
# Status
docker compose ps postgres

# Testar conexão
docker compose exec postgres pg_isready

# Ver logs
docker compose logs postgres

# Resetar (CUIDADO!)
docker compose down -v
docker compose up -d
```

### Porta em uso
```bash
# Ver o que está usando a porta
sudo lsof -i :8000
sudo lsof -i :8501

# Matar processo
sudo kill -9 <PID>
```

### Espaço em disco cheio
```bash
# Ver uso
df -h

# Limpar Docker
docker system prune -a

# Limpar logs antigos
sudo journalctl --vacuum-time=7d

# Limpar backups antigos
find /home/deploy/backups -mtime +30 -delete
```

---

## 📊 Pipeline

### Executar
```bash
# Modo liquid (63 ativos B3)
docker compose exec backend python scripts/run_pipeline.py --mode liquid

# Modo test (5 ativos)
docker compose exec backend python scripts/run_pipeline.py --mode test

# Ticker específico
docker compose exec backend python scripts/run_pipeline.py --mode manual --tickers PETR4.SA

# Ver logs
tail -f logs/pipeline.log
```

### Agendar (Cron)
```bash
# Editar crontab
crontab -e

# Executar diariamente às 18h
0 18 * * * cd /home/deploy/seu-repo && docker compose exec -T backend python scripts/run_pipeline.py --mode liquid >> /home/deploy/logs/pipeline.log 2>&1
```

---

## 🔐 Segurança

### Firewall
```bash
# Status
sudo ufw status

# Permitir porta
sudo ufw allow 8000/tcp

# Bloquear porta
sudo ufw deny 8000/tcp

# Resetar
sudo ufw reset
```

### Fail2ban
```bash
# Status
sudo fail2ban-client status

# Ver bans
sudo fail2ban-client status sshd

# Desbanir IP
sudo fail2ban-client set sshd unbanip <IP>
```

---

## 📝 Variáveis de Ambiente

### Editar
```bash
# Editar .env
nano .env

# Recarregar
docker compose down
docker compose up -d
```

### Essenciais
```bash
DATABASE_URL=postgresql://user:pass@host:5432/db
FMP_API_KEY=sua_chave
MOMENTUM_WEIGHT=0.4
QUALITY_WEIGHT=0.3
VALUE_WEIGHT=0.3
```

---

## 🆘 Comandos de Emergência

### Parar tudo
```bash
docker compose down
sudo systemctl stop nginx
```

### Reiniciar tudo
```bash
sudo reboot
```

### Restaurar backup
```bash
./deploy/restore-db.sh /path/to/backup.sql.gz
```

### Rollback código
```bash
git log --oneline
git checkout <commit-hash>
docker compose up -d --build
```

---

## 📞 URLs Úteis

### Documentação
- Docker: https://docs.docker.com
- Nginx: https://nginx.org/en/docs
- Certbot: https://certbot.eff.org
- Railway: https://docs.railway.app

### Ferramentas
- UptimeRobot: https://uptimerobot.com
- Sentry: https://sentry.io
- Papertrail: https://papertrailapp.com

---

## 💾 Backup Rápido

```bash
# Tudo em um comando
docker compose exec -T postgres pg_dump -U quant_user quant_ranker | gzip > backup_$(date +%Y%m%d).sql.gz
```

---

## 🎯 Checklist Diário

```bash
# 1. Verificar saúde
curl http://localhost:8000/health

# 2. Ver logs
docker compose logs --tail=50

# 3. Verificar recursos
docker stats --no-stream

# 4. Verificar disco
df -h

# 5. Verificar backups
ls -lh /home/deploy/backups/ | tail -5
```

---

**Salve este arquivo para referência rápida!**
