#!/bin/bash

# Script de Setup Automático para VPS
# Sistema de Ranking Quantitativo
# Ubuntu 22.04 LTS

set -e  # Exit on error

echo "=================================================="
echo "Setup VPS - Sistema de Ranking Quantitativo"
echo "=================================================="
echo ""

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Função para print colorido
print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}ℹ $1${NC}"
}

# Verificar se é root
if [ "$EUID" -ne 0 ]; then 
    print_error "Por favor, execute como root (sudo)"
    exit 1
fi

print_info "Iniciando setup do servidor..."
echo ""

# 1. Atualizar sistema
print_info "1/10 Atualizando sistema..."
apt update && apt upgrade -y
print_success "Sistema atualizado"
echo ""

# 2. Instalar dependências básicas
print_info "2/10 Instalando dependências básicas..."
apt install -y \
    curl \
    wget \
    git \
    vim \
    htop \
    ufw \
    fail2ban \
    unzip \
    software-properties-common \
    apt-transport-https \
    ca-certificates \
    gnupg \
    lsb-release
print_success "Dependências instaladas"
echo ""

# 3. Instalar Docker
print_info "3/10 Instalando Docker..."
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    rm get-docker.sh
    print_success "Docker instalado"
else
    print_info "Docker já está instalado"
fi
echo ""

# 4. Instalar Docker Compose
print_info "4/10 Instalando Docker Compose..."
apt install -y docker-compose-plugin
print_success "Docker Compose instalado"
echo ""

# 5. Criar usuário deploy
print_info "5/10 Configurando usuário deploy..."
if ! id "deploy" &>/dev/null; then
    adduser --disabled-password --gecos "" deploy
    usermod -aG docker deploy
    usermod -aG sudo deploy
    
    # Permitir sudo sem senha para deploy
    echo "deploy ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers.d/deploy
    
    print_success "Usuário deploy criado"
else
    print_info "Usuário deploy já existe"
fi
echo ""

# 6. Configurar firewall
print_info "6/10 Configurando firewall..."
ufw --force enable
ufw default deny incoming
ufw default allow outgoing
ufw allow 22/tcp comment 'SSH'
ufw allow 80/tcp comment 'HTTP'
ufw allow 443/tcp comment 'HTTPS'
ufw allow 8000/tcp comment 'Backend API'
ufw allow 8501/tcp comment 'Frontend Streamlit'
print_success "Firewall configurado"
echo ""

# 7. Configurar fail2ban
print_info "7/10 Configurando fail2ban..."
systemctl enable fail2ban
systemctl start fail2ban
print_success "Fail2ban configurado"
echo ""

# 8. Instalar Nginx
print_info "8/10 Instalando Nginx..."
apt install -y nginx
systemctl enable nginx
systemctl start nginx
print_success "Nginx instalado"
echo ""

# 9. Instalar Certbot (Let's Encrypt)
print_info "9/10 Instalando Certbot..."
apt install -y certbot python3-certbot-nginx
print_success "Certbot instalado"
echo ""

# 10. Criar estrutura de diretórios
print_info "10/10 Criando estrutura de diretórios..."
mkdir -p /home/deploy/logs
mkdir -p /home/deploy/backups
chown -R deploy:deploy /home/deploy
print_success "Diretórios criados"
echo ""

# Informações finais
echo ""
echo "=================================================="
print_success "Setup concluído com sucesso!"
echo "=================================================="
echo ""
echo "Próximos passos:"
echo ""
echo "1. Trocar para usuário deploy:"
echo "   su - deploy"
echo ""
echo "2. Clonar repositório:"
echo "   git clone https://github.com/seu-usuario/seu-repo.git"
echo "   cd seu-repo"
echo ""
echo "3. Configurar variáveis de ambiente:"
echo "   cp .env.example .env"
echo "   nano .env"
echo ""
echo "4. Iniciar aplicação:"
echo "   docker compose up -d --build"
echo ""
echo "5. Configurar Nginx (ver deploy/nginx.conf)"
echo ""
echo "6. Configurar SSL:"
echo "   sudo certbot --nginx -d seu-dominio.com"
echo ""
echo "=================================================="
echo ""

# Mostrar informações do sistema
print_info "Informações do sistema:"
echo "  IP: $(curl -s ifconfig.me)"
echo "  OS: $(lsb_release -d | cut -f2)"
echo "  Docker: $(docker --version)"
echo "  Docker Compose: $(docker compose version)"
echo ""

print_success "Servidor pronto para deploy!"
