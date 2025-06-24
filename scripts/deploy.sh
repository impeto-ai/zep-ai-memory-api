#!/bin/bash

# =================================================================
# ZEP AI MEMORY API - DEPLOYMENT SCRIPT
# =================================================================
# 
# Script para deploy da aplicação em produção
# Suporta deploy local via Docker e GCP Cloud Run
#
# =================================================================

set -e

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configurações
PROJECT_NAME="zep-ai-memory-api"
IMAGE_NAME="gcr.io/${GCP_PROJECT_ID}/${PROJECT_NAME}"
REGION="us-central1"

# Funções auxiliares
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Verificar pré-requisitos
check_prerequisites() {
    log_info "Verificando pré-requisitos..."
    
    # Verificar Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker não está instalado"
        exit 1
    fi
    
    # Verificar arquivo .env
    if [ ! -f ".env" ]; then
        log_error "Arquivo .env não encontrado. Copie env.production.example para .env"
        exit 1
    fi
    
    # Verificar variáveis obrigatórias
    source .env
    if [ -z "$API_SECRET_KEY" ] || [ "$API_SECRET_KEY" = "CHANGE_ME_TO_SECURE_32_PLUS_CHARACTER_SECRET_KEY" ]; then
        log_error "API_SECRET_KEY deve ser configurada no arquivo .env"
        exit 1
    fi
    
    if [ -z "$ZEP_API_KEY" ] || [ "$ZEP_API_KEY" = "your-production-zep-api-key" ]; then
        log_error "ZEP_API_KEY deve ser configurada no arquivo .env"
        exit 1
    fi
    
    log_success "Pré-requisitos verificados"
}

# Build da imagem Docker
build_image() {
    log_info "Construindo imagem Docker..."
    
    # Build com otimizações para produção
    docker build \
        --platform linux/amd64 \
        --tag ${PROJECT_NAME}:latest \
        --tag ${PROJECT_NAME}:$(date +%Y%m%d-%H%M%S) \
        --build-arg BUILDKIT_INLINE_CACHE=1 \
        .
    
    log_success "Imagem construída: ${PROJECT_NAME}:latest"
}

# Executar testes
run_tests() {
    log_info "Executando testes..."
    
    # Testes unitários
    docker run --rm \
        -v $(pwd):/app \
        -w /app \
        ${PROJECT_NAME}:latest \
        python -m pytest tests/ -v --cov=src --cov-report=term-missing
    
    # Testes de segurança
    docker run --rm \
        -v $(pwd):/app \
        -w /app \
        ${PROJECT_NAME}:latest \
        python -m bandit -r src/ -f json -o bandit-report.json || true
    
    # Verificação de tipos
    docker run --rm \
        -v $(pwd):/app \
        -w /app \
        ${PROJECT_NAME}:latest \
        python -m mypy src/ --ignore-missing-imports || true
    
    log_success "Testes concluídos"
}

# Deploy local via Docker Compose
deploy_local() {
    log_info "Iniciando deploy local..."
    
    # Parar containers existentes
    docker-compose down --remove-orphans
    
    # Iniciar serviços
    docker-compose up -d --build
    
    # Aguardar serviços ficarem prontos
    log_info "Aguardando serviços ficarem prontos..."
    sleep 30
    
    # Verificar health
    check_health "http://localhost:8080"
    
    log_success "Deploy local concluído!"
    log_info "API disponível em: http://localhost:8080"
    log_info "Documentação: http://localhost:8080/docs"
    log_info "Health Check: http://localhost:8080/health/detailed"
}

# Deploy para GCP Cloud Run
deploy_gcp() {
    log_info "Iniciando deploy para GCP Cloud Run..."
    
    # Verificar se gcloud está configurado
    if ! command -v gcloud &> /dev/null; then
        log_error "gcloud CLI não está instalado"
        exit 1
    fi
    
    if [ -z "$GCP_PROJECT_ID" ]; then
        log_error "GCP_PROJECT_ID deve ser definida"
        exit 1
    fi
    
    # Configurar projeto
    gcloud config set project $GCP_PROJECT_ID
    
    # Tag para GCR
    docker tag ${PROJECT_NAME}:latest ${IMAGE_NAME}:latest
    docker tag ${PROJECT_NAME}:latest ${IMAGE_NAME}:$(date +%Y%m%d-%H%M%S)
    
    # Push para GCR
    log_info "Enviando imagem para Google Container Registry..."
    docker push ${IMAGE_NAME}:latest
    docker push ${IMAGE_NAME}:$(date +%Y%m%d-%H%M%S)
    
    # Deploy para Cloud Run
    log_info "Fazendo deploy para Cloud Run..."
    gcloud run deploy ${PROJECT_NAME} \
        --image ${IMAGE_NAME}:latest \
        --platform managed \
        --region $REGION \
        --allow-unauthenticated \
        --memory 2Gi \
        --cpu 2 \
        --max-instances 100 \
        --concurrency 80 \
        --timeout 300 \
        --set-env-vars="DEBUG=false,LOG_LEVEL=INFO" \
        --set-env-vars="PROMETHEUS_ENABLED=true" \
        --set-env-vars="CACHE_ENABLED=true" \
        --set-env-vars="AUTH_ENABLED=true" \
        --set-env-vars="RATE_LIMIT_ENABLED=true" \
        --set-env-vars="SECURITY_HEADERS_ENABLED=true"
    
    # Obter URL do serviço
    SERVICE_URL=$(gcloud run services describe ${PROJECT_NAME} \
        --region $REGION \
        --format 'value(status.url)')
    
    # Verificar health
    check_health "$SERVICE_URL"
    
    log_success "Deploy para GCP concluído!"
    log_info "API disponível em: $SERVICE_URL"
    log_info "Documentação: $SERVICE_URL/docs"
    log_info "Health Check: $SERVICE_URL/health/detailed"
}

# Verificar saúde da aplicação
check_health() {
    local url=$1
    log_info "Verificando saúde da aplicação..."
    
    # Aguardar aplicação ficar pronta
    local max_attempts=30
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if curl -s -f "$url/health/live" > /dev/null; then
            log_success "Aplicação está funcionando!"
            break
        else
            log_info "Tentativa $attempt/$max_attempts - Aguardando aplicação..."
            sleep 10
            ((attempt++))
        fi
    done
    
    if [ $attempt -gt $max_attempts ]; then
        log_error "Aplicação não ficou pronta após $max_attempts tentativas"
        exit 1
    fi
    
    # Verificar health detalhado
    if health_response=$(curl -s "$url/health/detailed"); then
        status=$(echo $health_response | python3 -c "import sys, json; print(json.load(sys.stdin)['status'])")
        if [ "$status" = "healthy" ]; then
            log_success "Health check detalhado: $status"
        else
            log_warning "Health check detalhado: $status"
            echo $health_response | python3 -m json.tool
        fi
    fi
}

# Cleanup
cleanup() {
    log_info "Limpando recursos temporários..."
    
    # Remover imagens antigas (manter apenas as 5 mais recentes)
    docker images ${PROJECT_NAME} --format "table {{.Repository}}:{{.Tag}}\t{{.CreatedAt}}" | \
        tail -n +2 | sort -k2 -r | tail -n +6 | awk '{print $1}' | xargs -r docker rmi
    
    log_success "Cleanup concluído"
}

# Rollback (para Cloud Run)
rollback() {
    if [ -z "$GCP_PROJECT_ID" ]; then
        log_error "GCP_PROJECT_ID deve ser definida para rollback"
        exit 1
    fi
    
    log_info "Listando revisões disponíveis..."
    gcloud run revisions list --service ${PROJECT_NAME} --region $REGION
    
    echo -n "Digite o nome da revisão para rollback: "
    read revision_name
    
    if [ -n "$revision_name" ]; then
        log_info "Fazendo rollback para: $revision_name"
        gcloud run services update-traffic ${PROJECT_NAME} \
            --to-revisions=$revision_name=100 \
            --region $REGION
        
        log_success "Rollback concluído!"
    else
        log_error "Nome da revisão não fornecido"
        exit 1
    fi
}

# Menu principal
show_usage() {
    echo "Uso: $0 [COMANDO]"
    echo ""
    echo "Comandos disponíveis:"
    echo "  local     - Deploy local via Docker Compose"
    echo "  gcp       - Deploy para GCP Cloud Run"
    echo "  test      - Executar apenas testes"
    echo "  build     - Construir apenas imagem Docker"
    echo "  health    - Verificar saúde da aplicação"
    echo "  cleanup   - Limpar recursos temporários"
    echo "  rollback  - Fazer rollback no Cloud Run"
    echo ""
    echo "Exemplos:"
    echo "  $0 local     # Deploy local para desenvolvimento"
    echo "  $0 gcp       # Deploy em produção no GCP"
    echo "  $0 test      # Executar todos os testes"
}

# Main
main() {
    case ${1:-} in
        "local")
            check_prerequisites
            build_image
            run_tests
            deploy_local
            ;;
        "gcp")
            check_prerequisites
            build_image
            run_tests
            deploy_gcp
            cleanup
            ;;
        "test")
            check_prerequisites
            build_image
            run_tests
            ;;
        "build")
            check_prerequisites
            build_image
            ;;
        "health")
            if [ -n "${2:-}" ]; then
                check_health "$2"
            else
                check_health "http://localhost:8080"
            fi
            ;;
        "cleanup")
            cleanup
            ;;
        "rollback")
            rollback
            ;;
        *)
            show_usage
            exit 1
            ;;
    esac
}

# Executar
main "$@"