#!/usr/bin/env python3
"""
Script para rodar a Zep AI Memory API em desenvolvimento.
"""

import os
import uvicorn

if __name__ == "__main__":
    # Configurar para desenvolvimento
    os.environ.setdefault("DEBUG", "true")
    os.environ.setdefault("LOG_LEVEL", "DEBUG")
    os.environ.setdefault("RELOAD", "true")
    
    # Carregar configurações do .env se existir
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        print("python-dotenv não instalado. Configure as variáveis manualmente.")
    
    # Rodar servidor
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="debug",
        access_log=True
    ) 