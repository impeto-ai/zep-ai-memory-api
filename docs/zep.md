# Zep SDK - Documentação Completa

## O que é o Zep?

Zep é uma plataforma de memória para AI agents que utiliza **Knowledge Graphs Temporais** para armazenar e recuperar informações de forma inteligente. Diferente de soluções simples de RAG, o Zep:

- **Mantém contexto temporal**: Sabe quando fatos se tornaram válidos e inválidos
- **Funde dados**: Combina histórico de chat com dados de negócio
- **Aprende continuamente**: Atualiza conhecimento baseado em novas interações
- **Oferece busca híbrida**: Combina busca semântica com BM25

## Arquitetura Principal

### Knowledge Graph Temporal
- **Nós (Entities)**: Representam entidades como usuários, produtos, etc.
- **Arestas (Relationships)**: Representam relacionamentos e fatos
- **Atributos Temporais**: `valid_at`, `invalid_at`, `created_at`, `expired_at`

### Abstracões Principais

#### Users
- Representam usuários individuais do sistema
- Cada usuário tem seu próprio knowledge graph
- Suportam metadados customizados

#### Sessions  
- Threads de conversação de um usuário
- Múltiplas sessões por usuário
- Todas contribuem para o knowledge graph do usuário

#### Groups
- Graphs compartilhados entre usuários
- Útil para conhecimento organizacional
- Não incluído no `memory.context` automático

## APIs Principais

### Memory API (Alto Nível)

#### `memory.add()`
```python
await client.memory.add(
    session_id="session_123",
    messages=[
        Message(
            role="user",
            role_type="human", 
            content="Preciso cancelar minha assinatura"
        )
    ],
    return_context=True  # Otimização: retorna contexto imediatamente
)
```

#### `memory.get()`
```python
memory = await client.memory.get(session_id="session_123")
print(memory.context)  # String otimizada para prompt
print(memory.messages)  # Mensagens recentes
print(memory.relevant_facts)  # Fatos relevantes
```

### Graph API (Baixo Nível)

#### `graph.add()`
```python
# Dados de negócio estruturados
await client.graph.add(
    user_id=user_id,
    type="json",
    data={
        "account_status": "premium",
        "subscription_expires": "2024-12-31",
        "preferences": {"theme": "dark"}
    }
)

# Documentos não estruturados
await client.graph.add(
    user_id=user_id,
    type="text", 
    data="Contrato de prestação de serviços..."
)
```

#### `graph.search()`
```python
results = await client.graph.search(
    user_id=user_id,
    query="preferências de pagamento do usuário",
    limit=10
)
```

## Memory Context String

O `memory.context` é uma string otimizada contendo:

```
FACTS and ENTITIES represent relevant context to the current conversation.
# These are the most relevant facts and their valid date ranges
# format: FACT (Date range: from - to)
<FACTS>
- User prefers dark theme (2024-01-15 10:30:00+00:00 - present)
- Account status is premium (2024-01-01 00:00:00+00:00 - present)
- Last payment failed on card ending 1234 (2024-01-10 - 2024-01-15)
</FACTS>

# These are the most relevant entities
<ENTITIES>
- User: Premium subscriber with dark theme preference
- Payment Card 1234: Expired card that caused payment failure
</ENTITIES>
```

## Otimizações de Performance

### Reutilização de Cliente
```python
# ✅ Correto - uma instância global
client = AsyncZep(api_key=API_KEY)

# ❌ Evitar - nova instância a cada request  
def handle_request():
    client = AsyncZep(api_key=API_KEY)  # Cria nova conexão
```

### Batching Inteligente
```python
# Para conversas - usar memory.add
await client.memory.add(session_id, messages=[user_msg, ai_msg])

# Para documentos grandes - usar graph.add
await client.graph.add(user_id=user_id, type="text", data=document)
```

### Contexto Imediato
```python
# Otimização: pegar contexto direto do add
response = await client.memory.add(
    session_id=session_id,
    messages=messages,
    return_context=True  # Evita segundo request
)
context = response.context
```

## Casos de Uso Típicos

### 1. Chat Support Agent
```python
# Adicionar interação
await client.memory.add(session_id, messages=[
    Message(role="user", content="Não consigo fazer login"),
    Message(role="assistant", content="Vou verificar sua conta...")
])

# Buscar contexto para próxima resposta
memory = await client.memory.get(session_id)
# Usar memory.context no prompt do LLM
```

### 2. Sales Agent
```python
# Adicionar dados de CRM
await client.graph.add(user_id, type="json", data={
    "lead_score": 85,
    "interested_products": ["premium_plan"],
    "budget_range": "1000-5000"
})

# Buscar insights para pitch
results = await client.graph.search(
    user_id=user_id,
    query="interesse em produtos premium e orçamento"
)
```

### 3. Personal Assistant
```python
# Adicionar preferências do usuário
await client.graph.add(user_id, type="json", data={
    "preferences": {
        "meeting_time": "morning",
        "communication_style": "brief",
        "priorities": ["work", "family", "health"]
    }
})

# Recuperar para personalizar respostas
memory = await client.memory.get(session_id)
```

## Limitações e Considerações

### Limites de Tamanho
- Mensagens individuais: < 10K caracteres
- `graph.add`: < 10,000 caracteres
- Queries de busca: < 8,192 tokens (~32K caracteres)

### Boas Práticas para JSON
- Não muito grande (dividir em pedaços)
- Não muito aninhado (< 4 níveis)
- Compreensível isoladamente
- Representa entidade unificada

### Performance
- Retrieval: ~300ms P95
- Reutilizar cliente SDK
- Usar `return_context=True` quando possível
- Queries concisas e específicas

## Integração com Frameworks

### LangChain
```python
from langchain_community.chat_memory import ZepChatMemory

memory = ZepChatMemory(
    session_id=session_id,
    base_url="http://localhost:8000",
    api_key=api_key
)
```

### N8N (via REST API)
```javascript
// Nossa API REST wrapper permitirá:
POST /api/v1/memory/sessions/{session_id}/messages
GET /api/v1/memory/sessions/{session_id}/context
POST /api/v1/graph/users/{user_id}/data
GET /api/v1/graph/users/{user_id}/search
```

## Casos de Erro Comuns

### 1. Cliente Não Reutilizado
**Problema**: Criar nova instância a cada request
**Solução**: Singleton pattern ou dependency injection

### 2. Mensagens Muito Grandes  
**Problema**: Mensagem > 10K caracteres
**Solução**: Usar `graph.add` para documentos grandes

### 3. JSON Muito Complexo
**Problema**: JSON aninhado ou muito grande
**Solução**: Achatar e dividir em pedaços menores

### 4. Queries Genéricas
**Problema**: Busca vaga como "informações do usuário"
**Solução**: Queries específicas como "preferências de pagamento" 