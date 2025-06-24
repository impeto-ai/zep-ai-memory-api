#!/usr/bin/env python3
"""
Script para testar a Zep AI Memory API em funcionamento.
Execute depois que a API estiver rodando.
"""

import requests
import json
import time
from datetime import datetime

# Configurações
API_BASE = "http://localhost:8080"
USER_ID = "test_user_123"
SESSION_ID = "test_session_456"

def test_health_check():
    """Testa se a API está funcionando."""
    print("🔍 Testando Health Check...")
    
    response = requests.get(f"{API_BASE}/health/detailed")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ API está funcionando! Status: {data['status']}")
        print(f"📊 Checks: {data['checks']}")
        return True
    else:
        print(f"❌ API não está respondendo: {response.status_code}")
        return False

def test_add_memory():
    """Testa adicionar mensagens à memória."""
    print("\n🧠 Testando adicionar memória...")
    
    payload = {
        "messages": [
            {
                "role": "user",
                "role_type": "human",
                "content": "Olá! Meu nome é João e eu trabalho como desenvolvedor Python.",
                "metadata": {"timestamp": datetime.now().isoformat()}
            },
            {
                "role": "assistant", 
                "role_type": "ai",
                "content": "Olá João! Prazer em conhecê-lo. Vejo que você é desenvolvedor Python. Em que tipos de projetos você trabalha?",
                "metadata": {"timestamp": datetime.now().isoformat()}
            },
            {
                "role": "user",
                "role_type": "human", 
                "content": "Trabalho principalmente com APIs REST e integração com n8n. Adoro automatizar processos!",
                "metadata": {"timestamp": datetime.now().isoformat()}
            }
        ],
        "return_context": True
    }
    
    response = requests.post(
        f"{API_BASE}/api/v1/memory/sessions/{SESSION_ID}/messages",
        json=payload
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Memória adicionada! {data['messages_added']} mensagens")
        if data.get('context'):
            print(f"🎯 Contexto gerado: {data['context'][:200]}...")
        return True
    else:
        print(f"❌ Erro ao adicionar memória: {response.status_code}")
        print(f"Erro: {response.text}")
        return False

def test_get_context():
    """Testa recuperar contexto da memória."""
    print("\n📖 Testando recuperar contexto...")
    
    response = requests.get(f"{API_BASE}/api/v1/memory/sessions/{SESSION_ID}/context")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Contexto recuperado!")
        print(f"📝 Mensagens na sessão: {len(data.get('messages', []))}")
        print(f"🧠 Contexto: {data.get('context', 'Nenhum')[:300]}...")
        
        # Mostrar fatos relevantes se houver
        facts = data.get('relevant_facts', [])
        if facts:
            print(f"💡 Fatos relevantes: {len(facts)}")
            for fact in facts[:3]:  # Mostrar apenas os 3 primeiros
                print(f"   - {fact}")
        
        return True
    else:
        print(f"❌ Erro ao recuperar contexto: {response.status_code}")
        return False

def test_memory_search():
    """Testa busca na memória."""
    print("\n🔍 Testando busca na memória...")
    
    payload = {
        "query": "João desenvolvedor Python",
        "search_scope": "all",
        "limit": 5
    }
    
    response = requests.post(
        f"{API_BASE}/api/v1/memory/users/{USER_ID}/search",
        json=payload
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Busca realizada! {data['total_count']} resultados")
        
        results = data.get('results', [])
        for i, result in enumerate(results[:3]):  # Mostrar 3 primeiros
            print(f"   {i+1}. {result.get('content', 'N/A')[:100]}...")
            
        return True
    else:
        print(f"❌ Erro na busca: {response.status_code}")
        return False

def test_graph_data():
    """Testa adicionar dados ao graph."""
    print("\n🕸️ Testando Knowledge Graph...")
    
    payload = {
        "data": {
            "user_info": {
                "name": "João",
                "profession": "Desenvolvedor Python",
                "interests": ["APIs REST", "n8n", "automação"],
                "experience_level": "senior",
                "preferred_stack": ["Python", "FastAPI", "Docker"]
            }
        },
        "data_type": "json"
    }
    
    response = requests.post(
        f"{API_BASE}/api/v1/graph/users/{USER_ID}/data",
        json=payload
    )
    
    if response.status_code == 200:
        print("✅ Dados adicionados ao Knowledge Graph!")
        return True
    else:
        print(f"❌ Erro ao adicionar ao graph: {response.status_code}")
        return False

def test_session_stats():
    """Testa estatísticas da sessão."""
    print("\n📊 Testando estatísticas da sessão...")
    
    response = requests.get(f"{API_BASE}/api/v1/memory/sessions/{SESSION_ID}/stats")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Estatísticas recuperadas!")
        print(f"📝 Total de mensagens: {data.get('total_messages', 0)}")
        print(f"💡 Total de fatos: {data.get('total_facts', 0)}")
        print(f"📏 Tamanho do contexto: {data.get('context_length', 0)} chars")
        return True
    else:
        print(f"❌ Erro ao obter stats: {response.status_code}")
        return False

def main():
    """Executa todos os testes."""
    print("🚀 TESTANDO ZEP AI MEMORY API")
    print("=" * 50)
    
    # Verificar se API está online
    if not test_health_check():
        print("\n❌ API não está funcionando. Verifique se está rodando em http://localhost:8080")
        return
    
    # Executar testes sequenciais
    tests = [
        test_add_memory,
        test_get_context, 
        test_memory_search,
        test_graph_data,
        test_session_stats
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
            time.sleep(1)  # Pequena pausa entre testes
        except Exception as e:
            print(f"❌ Erro no teste: {e}")
    
    print(f"\n🎯 RESULTADO: {passed}/{total} testes passaram!")
    
    if passed == total:
        print("🔥 TODOS OS TESTES PASSARAM! API está funcionando perfeitamente!")
    else:
        print("⚠️ Alguns testes falharam. Verifique os logs acima.")
    
    print(f"\n📖 Acesse a documentação em: {API_BASE}/docs")
    print(f"🔍 Health check detalhado: {API_BASE}/health/detailed")

if __name__ == "__main__":
    main() 