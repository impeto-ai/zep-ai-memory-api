#!/bin/bash

# 🚀 Setup automático da Zep AI Memory API
# Para macOS e Linux

set -e  # Exit on any error

echo "🚀 ZEP AI MEMORY API - Setup Automático"
echo "======================================="

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 1. Verificar pré-requisitos
print_status "Verificando pré-requisitos..."

# Verificar Docker
if ! command -v docker &> /dev/null; then
    print_error "Docker não está instalado!"
    echo "Instale Docker: https://docs.docker.com/get-docker/"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    print_error "Docker Compose não está instalado!"
    echo "Instale Docker Compose: https://docs.docker.com/compose/install/"
    exit 1
fi

print_success "Docker e Docker Compose encontrados!"

# 2. Verificar se Docker está rodando
if ! docker info &> /dev/null; then
    print_error "Docker não está rodando!"
    echo "Inicie o Docker Desktop ou daemon do Docker"
    exit 1
fi

print_success "Docker está rodando!"

# 3. Configurar ambiente
print_status "Configurando ambiente..."

if [ ! -f .env ]; then
    cp env.example .env
    print_success "Arquivo .env criado!"
    
    print_warning "IMPORTANTE: Edite o arquivo .env com suas configurações:"
    echo "  - ZEP_API_KEY: Sua chave do Zep"
    echo "  - API_SECRET_KEY: Sua chave secreta (min 32 chars)"
    echo ""
    read -p "Pressione Enter para continuar após editar o .env..."
else
    print_success "Arquivo .env já existe!"
fi

# 4. Criar diretórios necessários
print_status "Criando diretórios..."
mkdir -p logs
mkdir -p data/postgres
mkdir -p data/redis
print_success "Diretórios criados!"

# 5. Baixar imagens Docker
print_status "Baixando imagens Docker..."
docker-compose pull

# 6. Subir os serviços
print_status "Subindo serviços..."
docker-compose up -d

# 7. Aguardar serviços ficarem prontos
print_status "Aguardando serviços ficarem prontos..."

wait_for_service() {
    local service_name=$1
    local url=$2
    local max_attempts=30
    local attempt=1

    while [ $attempt -le $max_attempts ]; do
        if curl -s -f "$url" > /dev/null 2>&1; then
            print_success "$service_name está pronto!"
            return 0
        fi
        
        echo -n "."
        sleep 2
        ((attempt++))
    done
    
    print_error "$service_name não ficou pronto em tempo hábil"
    return 1
}

echo -n "Aguardando Zep Community Edition"
wait_for_service "Zep" "http://localhost:8000/healthz"

echo -n "Aguardando nossa API"  
wait_for_service "Zep AI Memory API" "http://localhost:8080/health/live"

# 8. Verificar status
print_status "Verificando status dos serviços..."
docker-compose ps

# 9. Instalar dependências Python para testes (opcional)
if command -v python3 &> /dev/null; then
    print_status "Instalando dependências Python para testes..."
    pip3 install requests > /dev/null 2>&1 || pip install requests > /dev/null 2>&1
    print_success "Dependências instaladas!"
fi

# 10. Executar testes básicos
print_status "Executando testes básicos..."
if command -v python3 &> /dev/null; then
    python3 test_api.py
else
    python test_api.py
fi

echo ""
echo "🎉 SETUP COMPLETO!"
echo "=================="
echo ""
echo "🔗 LINKS ÚTEIS:"
echo "  📖 Documentação API: http://localhost:8080/docs"
echo "  🔍 Health Check:     http://localhost:8080/health/detailed"
echo "  📊 Métricas:         http://localhost:8080/metrics"
echo "  🧠 Zep Community:    http://localhost:8000"
echo ""
echo "🐳 GERENCIAR SERVIÇOS:"
echo "  docker-compose ps                 # Ver status"
echo "  docker-compose logs -f zep-api    # Ver logs da API"
echo "  docker-compose down               # Parar tudo"
echo "  docker-compose up -d              # Subir novamente"
echo ""
echo "🧪 EXECUTAR TESTES:"
echo "  python3 test_api.py               # Testar API"
echo ""
print_success "API está rodando e pronta para uso! 🚀" 