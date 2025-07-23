#!/usr/bin/env python3
"""
🎤 WHISPERSILENT - APLICAÇÃO ÚNICA UNIFICADA
===========================================

Esta é a aplicação única que integra TODAS as funcionalidades do WhisperSilent:
- Transcrição em tempo real com 12+ engines
- API REST completa (25+ endpoints)
- WebSocket para streaming em tempo real
- Monitoramento de saúde do sistema
- Agregação inteligente por hora
- Fallback automático online/offline
- Identificação de falantes
- Múltiplos modos de operação

EXECUÇÃO:
    python3 whispersilent_unified.py

Este arquivo é um wrapper que chama a aplicação principal src/main.py
com todas as funcionalidades integradas.
"""

import os
import sys
import subprocess
from pathlib import Path

# Verificar se estamos no diretório correto
current_dir = Path(__file__).parent
main_script = current_dir / "src" / "main.py"

if not main_script.exists():
    print("❌ Erro: Arquivo src/main.py não encontrado!")
    print(f"   Certifique-se de estar no diretório: {current_dir}")
    sys.exit(1)

print("🎤 WHISPERSILENT - APLICAÇÃO ÚNICA UNIFICADA")
print("=" * 50)
print()
print("🚀 Iniciando aplicação unificada com todas as funcionalidades...")
print("📍 Localização:", main_script)
print()

# Executar a aplicação principal
try:
    # Passar todos os argumentos da linha de comando
    cmd = [sys.executable, str(main_script)] + sys.argv[1:]
    subprocess.run(cmd, cwd=current_dir)
except KeyboardInterrupt:
    print("\n👋 Aplicação interrompida pelo usuário")
except Exception as e:
    print(f"❌ Erro ao executar aplicação: {e}")
    sys.exit(1)