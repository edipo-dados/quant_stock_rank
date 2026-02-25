# Índice de Deploy

Documentação completa para deploy e manutenção do sistema.

## 🚀 Guias de Deploy

### Para Iniciantes
- **[SETUP_NOVO_EC2.md](SETUP_NOVO_EC2.md)** ⭐ COMECE AQUI
  - Guia passo a passo simples
  - Instalação do Docker e Docker Compose
  - Deploy completo em novo servidor EC2
  - Comandos prontos para copiar e colar

### Documentação Completa
- **[EC2_DEPLOY.md](EC2_DEPLOY.md)**
  - Guia detalhado de deploy em EC2
  - Configuração de Nginx e SSL
  - Backup e restore
  - Troubleshooting avançado

### Referência Rápida
- **[QUICK_REFERENCE.md](QUICK_REFERENCE.md)**
  - Comandos mais usados
  - Atalhos úteis
  - Checklist de verificação

## 📋 Ordem Recomendada

### 1. Primeiro Deploy
1. Ler [SETUP_NOVO_EC2.md](SETUP_NOVO_EC2.md)
2. Seguir passo a passo
3. Testar aplicação
4. Configurar cron job

### 2. Configuração Avançada
1. Ler [EC2_DEPLOY.md](EC2_DEPLOY.md)
2. Configurar Nginx (se usar domínio)
3. Configurar SSL com Certbot
4. Configurar backups automáticos

### 3. Manutenção
1. Consultar [QUICK_REFERENCE.md](QUICK_REFERENCE.md)
2. Executar backups regulares
3. Monitorar logs
4. Atualizar código quando necessário

## 🛠️ Scripts Disponíveis

- **backup-db.sh** - Backup manual do PostgreSQL
- **restore-db.sh** - Restaurar backup
- **vps-setup.sh** - Setup automatizado (avançado)
- **nginx.conf** - Configuração exemplo do Nginx

## 📊 Fluxo de Deploy

```
┌─────────────────┐
│  Criar EC2      │
│  Ubuntu 22.04   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Instalar Docker │
│ Docker Compose  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Clonar Repo     │
│ Configurar .env │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ docker-compose  │
│ up -d           │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Testar          │
│ Aplicação       │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Configurar Cron │
│ Backups         │
└─────────────────┘
```

## 🔧 Requisitos

### Servidor EC2
- **OS**: Ubuntu 22.04 LTS
- **Tipo**: t2.medium ou superior
- **Storage**: 20GB+ SSD
- **RAM**: 4GB+
- **Portas**: 22, 80, 443, 8000, 8501

### Software
- Docker 20.10+
- Docker Compose 2.0+
- Git 2.0+

### Credenciais Necessárias
- FMP API Key
- Google Gemini API Key
- Chave SSH (.pem)

## 📝 Checklist de Deploy

- [ ] EC2 criado e acessível via SSH
- [ ] Security Group configurado (portas abertas)
- [ ] Docker instalado
- [ ] Docker Compose instalado
- [ ] Git instalado
- [ ] Repositório clonado
- [ ] Arquivo .env.production criado
- [ ] API keys configuradas
- [ ] Containers rodando (docker-compose ps)
- [ ] Backend respondendo (curl health)
- [ ] Frontend acessível (navegador)
- [ ] Pipeline executado com sucesso
- [ ] Dados no banco verificados
- [ ] Cron job configurado
- [ ] Backup automático configurado

## 🆘 Problemas Comuns

### Containers não sobem
Ver: [EC2_DEPLOY.md - Troubleshooting](EC2_DEPLOY.md#troubleshooting)

### Banco não conecta
Ver: [SETUP_NOVO_EC2.md - Problemas](SETUP_NOVO_EC2.md#problemas)

### Pipeline falha
Ver logs: `docker logs quant-ranker-backend`

## 📚 Documentação Relacionada

- [README.md](../README.md) - Visão geral do projeto
- [docs/INDEX.md](../docs/INDEX.md) - Documentação técnica
- [CHANGELOG.md](../CHANGELOG.md) - Histórico de versões

## 🔄 Atualizações

Para atualizar o sistema em produção:

```bash
cd ~/quant_stock_rank
git pull
docker-compose build --no-cache
docker-compose down
docker-compose up -d
```

## 📞 Suporte

Para problemas não cobertos nesta documentação:
1. Verificar logs: `docker logs quant-ranker-backend`
2. Consultar troubleshooting nos guias
3. Verificar issues no GitHub

---

**Última atualização**: 24/02/2026
