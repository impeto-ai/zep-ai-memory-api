# 🧠 Zep AI Memory API

**API REST enterprise-grade para Zep AI Memory platform**

Uma API REST wrapper moderna e escalável para o Zep SDK, projetada especificamente para integração com n8n e outras plataformas de automação.

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue.svg)](https://docker.com)
[![GCP](https://img.shields.io/badge/GCP-Optimized-orange.svg)](https://cloud.google.com)

## 🎯 Visão Geral

Esta API transforma o poderoso Zep SDK em endpoints HTTP prontos para consumo, permitindo que qualquer sistema acesse funcionalidades avançadas de memória para AI agents através de chamadas REST simples.

### ✨ Principais Características

- **🚀 Performance Otimizada**: Cliente Zep reutilizável com connection pooling
- **📊 Observabilidade Completa**: Métricas Prometheus, logging estruturado, health checks
- **🔒 Segurança Enterprise**: Validação robusta, rate limiting, autenticação JWT
- **🏗️ Arquitetura Limpa**: Modular, testável e facilmente extensível
- **☁️ Cloud Native**: Pronto para deploy no GCP com Kubernetes
- **📖 Documentação Automática**: OpenAPI/Swagger gerado automaticamente

## 🛠️ Stack Tecnológico

- **Backend**: Python 3.11+ com FastAPI
- **Cliente Zep**: zep-python SDK otimizado
- **Cache**: Redis para performance
- **Monitoramento**: Prometheus + Grafana
- **Deploy**: Docker + Google Cloud Platform
- **Testes**: pytest com cobertura completa

## 🚀 Quick Start

### Pré-requisitos

- Python 3.11+
- Docker e Docker Compose
- Conta no GCP (para deploy em produção)

### 1. Clone e Setup

```bash
git clone <repository-url>
cd zep_ai_memory_api

# Copiar configurações
cp env.example .env
# Editar .env com suas configurações
```

### 2. Desenvolvimento Local

```bash
# Subir todos os serviços (Zep + PostgreSQL + Redis + API)
docker-compose up -d

# Verificar status
docker-compose ps

# Ver logs da API
docker-compose logs -f zep-api
```

### 3. Acesso à API

- **API**: http://localhost:8080
- **Documentação**: http://localhost:8080/docs
- **Health Check**: http://localhost:8080/health/detailed
- **Zep Community**: http://localhost:8000
- **Métricas**: http://localhost:8080/metrics

## 📋 Endpoints Principais

### Memory API (Alto Nível)

```http
# Adicionar mensagens à memória
POST /api/v1/memory/sessions/{session_id}/messages

# Obter contexto da memória
GET /api/v1/memory/sessions/{session_id}/context

# Buscar na memória do usuário
POST /api/v1/memory/users/{user_id}/search
```

### Graph API (Baixo Nível)

```http
# Adicionar dados ao knowledge graph
POST /api/v1/graph/users/{user_id}/data

# Buscar no knowledge graph
POST /api/v1/graph/users/{user_id}/search

# Listar entidades extraídas
GET /api/v1/graph/users/{user_id}/entities
```

### Monitoramento

```http
# Health checks
GET /health/live      # Liveness probe
GET /health/ready     # Readiness probe  
GET /health/detailed  # Status completo

# Métricas
GET /metrics          # Prometheus format
GET /health/metrics-summary  # JSON summary
```

## 🔧 Configuração

### Variáveis de Ambiente Principais

```bash
# API Configuration
API_SECRET_KEY="your-super-secret-key-min-32-chars"
DEBUG=false
LOG_LEVEL="INFO"

# Zep Configuration  
ZEP_API_URL="http://localhost:8000"
ZEP_API_KEY="your-zep-api-key"

# Cache (Redis)
REDIS_URL="redis://localhost:6379" 
CACHE_ENABLED=true

# Monitoring
PROMETHEUS_ENABLED=true
```

Ver `env.example` para configuração completa.

## 🏗️ Arquitetura

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   n8n / Apps    │───▶│  Zep Memory API │───▶│   Zep Platform  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
                        ┌─────────────────┐
                        │ Redis + Metrics │
                        └─────────────────┘
```

### Componentes

- **FastAPI App**: Servidor HTTP com validação automática
- **Zep Client**: Wrapper otimizado com connection pooling
- **Redis Cache**: Cache de respostas e sessões ativas
- **Prometheus**: Métricas de performance e uso
- **Health Checks**: Probes para Kubernetes

## 📊 Monitoramento e Observabilidade

### Métricas Coletadas

- **Request Metrics**: Volume, latência, taxa de erro
- **Zep Operations**: Operações de memory e graph
- **Cache Performance**: Hit ratio, latência
- **System Health**: CPU, memória, uptime

### Health Checks

- **Liveness**: `/health/live` - Processo funcionando
- **Readiness**: `/health/ready` - Pronto para tráfego
- **Detailed**: `/health/detailed` - Status completo

## 🚀 Deploy no GCP

### 1. Cloud Run (Recomendado)

```bash
# Build e push da imagem
docker build -t gcr.io/[PROJECT]/zep-ai-memory-api .
docker push gcr.io/[PROJECT]/zep-ai-memory-api

# Deploy no Cloud Run
gcloud run deploy zep-ai-memory-api \
  --image gcr.io/[PROJECT]/zep-ai-memory-api \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars="ZEP_API_URL=your-zep-url"
```

### 2. GKE (Kubernetes)

Ver arquivos em `deploy/k8s/` (TODO).

## 🧪 Testes

```bash
# Executar testes
docker-compose exec zep-api pytest

# Com cobertura
docker-compose exec zep-api pytest --cov=src

# Load testing
docker-compose exec zep-api locust -f tests/load/locustfile.py
```

## 📈 Performance

### Benchmarks Esperados

- **Latência**: < 200ms para operações de memória
- **Throughput**: > 1000 req/s por instância
- **Cache Hit Ratio**: > 80% para queries frequentes

### Otimizações Implementadas

- Cliente Zep singleton com connection pooling
- Cache Redis para respostas frequentes
- Compressão gzip automática
- Validação Pydantic otimizada

## 🔒 Segurança

- **Validação**: Entrada sanitizada via Pydantic
- **Rate Limiting**: Proteção contra abuse
- **Logs**: Structured logging sem dados sensíveis
- **Docker**: Container não-root, minimal attack surface

## 🤝 Contribuição

1. Fork o projeto
2. Crie uma branch (`git checkout -b feature/nova-funcionalidade`)
3. Commit suas mudanças (`git commit -am 'Adiciona nova funcionalidade'`)
4. Push para a branch (`git push origin feature/nova-funcionalidade`)
5. Abra um Pull Request

## 📄 Licença

MIT License. Ver `LICENSE` para detalhes.

## 🙋‍♂️ Suporte

- **Documentação**: http://localhost:8080/docs
- **Issues**: GitHub Issues
- **Discussões**: GitHub Discussions

---

**🚀 Pronto para revolucionar a memória dos seus AI agents!** 