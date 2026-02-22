# Guia de Conexão ao Banco de Dados

## ⚡ Opção Rápida: SQLite (Sem Docker)

**Melhor para:** Começar rapidamente, desenvolvimento local, testes

Se você não tem Docker instalado, pode usar SQLite:

### 1. Configure o .env para SQLite

Edite o arquivo `.env` e altere a linha `DATABASE_URL`:

```bash
# Para SQLite (arquivo local - dados persistem)
DATABASE_URL=sqlite:///./quant_ranker.db
```

### 2. Inicialize as tabelas

```bash
python scripts/init_db.py
```

### 3. Verificar conexão

```bash
python scripts/check_db.py
```

✅ Pronto! Você está usando SQLite localmente.

**Vantagens:**
- ✅ Não precisa instalar nada
- ✅ Funciona imediatamente  
- ✅ Perfeito para desenvolvimento

**Limitações:**
- ⚠️ Menos recursos que PostgreSQL
- ⚠️ Não recomendado para produção

---

## 🐳 Opção Completa: PostgreSQL com Docker

**Melhor para:** Produção, desenvolvimento em equipe, recursos avançados

### Pré-requisito: Instalar Docker

**Windows:**
1. Baixe Docker Desktop: https://www.docker.com/products/docker-desktop
2. Instale e reinicie o computador
3. Abra Docker Desktop

**Linux:**
```bash
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
```

**Mac:**
1. Baixe Docker Desktop: https://www.docker.com/products/docker-desktop
2. Instale e abra o aplicativo

### 1. Iniciar PostgreSQL

```bash
docker-compose up -d postgres
```

### 2. Configure o .env

Certifique-se que o `.env` tem:

```bash
DATABASE_URL=postgresql://user:password@localhost:5432/quant_ranker
```

### 3. Inicializar tabelas

```bash
python scripts/init_db.py
```

### 4. Verificar conexão

```bash
python scripts/check_db.py
```

**Credenciais:**
- Host: `localhost`
- Porta: `5432`
- Usuário: `user`
- Senha: `password`
- Database: `quant_ranker`

---

## 📊 Comparação

| Característica | SQLite | PostgreSQL |
|---------------|--------|------------|
| Instalação | ✅ Nenhuma | Docker necessário |
| Velocidade setup | ✅ Imediato | ~2 minutos |
| Performance | Boa | Excelente |
| Recursos | Básicos | Avançados |
| Produção | ❌ Não | ✅ Sim |
| Desenvolvimento | ✅ Sim | ✅ Sim |

---

## 🔧 Comandos Úteis

### SQLite

```bash
# Ver o arquivo do banco
dir quant_ranker.db

# Conectar via sqlite3 (se instalado)
sqlite3 quant_ranker.db

# Dentro do sqlite3:
.tables          # Listar tabelas
.schema          # Ver schema
SELECT * FROM raw_prices_daily LIMIT 10;
.quit            # Sair
```

### PostgreSQL

```bash
# Iniciar banco
docker-compose up -d postgres

# Parar banco
docker-compose down

# Ver logs
docker-compose logs -f postgres

# Conectar via psql
docker exec -it quant_ranker_db psql -U user -d quant_ranker

# Dentro do psql:
\dt              # Listar tabelas
\d raw_prices_daily  # Ver estrutura
SELECT * FROM raw_prices_daily LIMIT 10;
\q               # Sair

# Verificar status
python scripts/check_db.py
```

---

## 🚀 Recomendação

1. **Começando agora?** Use SQLite
2. **Indo para produção?** Migre para PostgreSQL
3. **Trabalhando em equipe?** Use PostgreSQL desde o início

Para migrar de SQLite para PostgreSQL:
1. Instale Docker
2. Altere `DATABASE_URL` no `.env`
3. Execute `python scripts/init_db.py`
4. Seus dados precisarão ser re-ingeridos

---

## ❓ Troubleshooting

### SQLite

**Erro: "unable to open database file"**
- Verifique permissões da pasta
- Certifique-se que o caminho no DATABASE_URL está correto

### PostgreSQL

**Erro: "Connection refused"**
- Verifique se Docker está rodando: `docker ps`
- Inicie o banco: `docker-compose up -d postgres`

**Erro: "Database does not exist"**
- O banco é criado automaticamente pelo Docker
- Verifique o docker-compose.yml

**Erro: "Authentication failed"**
- Verifique as credenciais no `.env`
- Use: `user` / `password`

**Porta 5432 já em uso**
- Outro PostgreSQL está rodando
- Pare o outro serviço ou mude a porta no docker-compose.yml
