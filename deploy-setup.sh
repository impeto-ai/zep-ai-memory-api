#!/bin/bash
echo "🚀 Setup GCP Deploy para Zep AI Memory API"
echo "============================================"

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Função para print colorido
print_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
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

print_step "1. Verificando dependências..."

# Verificar se gcloud está instalado
if ! command -v gcloud &> /dev/null; then
    print_error "Google Cloud CLI não encontrado!"
    echo "Instale com: brew install google-cloud-sdk"
    exit 1
fi

# Verificar se docker está instalado
if ! command -v docker &> /dev/null; then
    print_error "Docker não encontrado!"
    echo "Instale Docker Desktop: https://docs.docker.com/desktop/install/mac-install/"
    exit 1
fi

print_success "Dependências OK!"

print_step "2. Configurando projeto GCP..."

# Listar projetos disponíveis
echo "Projetos GCP disponíveis:"
gcloud projects list --format="table(projectId,name,projectNumber)"

echo ""
read -p "Digite o ID do projeto GCP: " PROJECT_ID

if [ -z "$PROJECT_ID" ]; then
    print_error "Project ID é obrigatório!"
    exit 1
fi

# Configurar projeto padrão
gcloud config set project $PROJECT_ID
print_success "Projeto configurado: $PROJECT_ID"

print_step "3. Habilitando APIs necessárias..."

# APIs necessárias para Cloud Run
APIS=(
    "cloudbuild.googleapis.com"
    "run.googleapis.com"
    "containerregistry.googleapis.com"
    "artifactregistry.googleapis.com"
)

for api in "${APIS[@]}"; do
    echo "Habilitando $api..."
    gcloud services enable $api
done

print_success "APIs habilitadas!"

print_step "4. Criando Service Account para GitHub Actions..."

SA_NAME="github-actions-sa"
SA_EMAIL="$SA_NAME@$PROJECT_ID.iam.gserviceaccount.com"

# Criar service account se não existir
if ! gcloud iam service-accounts describe $SA_EMAIL &> /dev/null; then
    gcloud iam service-accounts create $SA_NAME \
        --display-name="GitHub Actions Service Account" \
        --description="Service Account para deploy via GitHub Actions"
    print_success "Service Account criado: $SA_EMAIL"
else
    print_warning "Service Account já existe: $SA_EMAIL"
fi

# Atribuir roles necessários
ROLES=(
    "roles/run.admin"
    "roles/storage.admin"
    "roles/iam.serviceAccountUser"
    "roles/cloudbuild.builds.editor"
)

for role in "${ROLES[@]}"; do
    echo "Atribuindo role $role..."
    gcloud projects add-iam-policy-binding $PROJECT_ID \
        --member="serviceAccount:$SA_EMAIL" \
        --role="$role"
done

print_success "Roles atribuídos!"

print_step "5. Gerando chave da Service Account..."

KEY_FILE="gcp-sa-key.json"
gcloud iam service-accounts keys create $KEY_FILE \
    --iam-account=$SA_EMAIL

print_success "Chave gerada: $KEY_FILE"

print_step "6. Preparando variáveis para GitHub Secrets..."

echo ""
echo "=================================="
echo "🔐 CONFIGURE OS SEGUINTES SECRETS NO GITHUB:"
echo "=================================="
echo ""
echo "1. GCP_PROJECT_ID:"
echo "   $PROJECT_ID"
echo ""
echo "2. GCP_SA_KEY:"
echo "   $(cat $KEY_FILE | base64)"
echo ""
echo "3. API_SECRET_KEY (32+ caracteres):"
echo "   $(openssl rand -hex 32)"
echo ""
echo "4. ZEP_API_KEY:"
echo "   sua-zep-api-key-aqui"
echo ""
echo "5. ZEP_API_URL:"
echo "   https://api.getzep.com  # ou sua URL do Zep"
echo ""
echo "6. CORS_ORIGINS:"
echo "   https://seudominio.com,https://app.seudominio.com"
echo ""
echo "7. CACHE_ENABLED:"
echo "   true"
echo ""
echo "8. REDIS_URL:"
echo "   redis://YOUR_REDIS_INSTANCE_IP:6379  # Configure Cloud Memorystore"
echo ""
echo "=================================="
echo "📚 Como adicionar secrets no GitHub:"
echo "1. Vá para Settings > Secrets and variables > Actions"
echo "2. Clique em 'New repository secret'"
echo "3. Adicione cada secret acima"
echo "=================================="

print_step "7. Limpando arquivos temporários..."
rm -f $KEY_FILE
print_success "Cleanup concluído!"

echo ""
print_success "Setup completo! Configure os secrets no GitHub e faça push para main/master."
echo ""
echo "🚀 Para deploy manual local, use:"
echo "   ./deploy-local.sh"