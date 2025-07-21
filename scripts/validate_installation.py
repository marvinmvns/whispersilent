#!/usr/bin/env python3
"""
Script de validação final da instalação WhisperSilent.
Verifica se todos os componentes estão funcionando corretamente.
"""

import sys
import os
import subprocess
import json
from pathlib import Path

def check_file_permissions():
    """Verifica se os scripts têm as permissões corretas"""
    print("🔐 Verificando permissões dos arquivos...")
    
    scripts_to_check = [
        'scripts/test_microphone_basic.py',
        'scripts/test_transcription_api.py', 
        'scripts/test_complete_system.py',
        'scripts/install_and_test.sh',
        'scripts/detect_audio_devices.py'
    ]
    
    all_good = True
    for script in scripts_to_check:
        script_path = Path(script)
        if script_path.exists():
            if os.access(script_path, os.X_OK):
                print(f"   ✅ {script}")
            else:
                print(f"   ❌ {script} (não executável)")
                all_good = False
        else:
            print(f"   ❌ {script} (não encontrado)")
            all_good = False
    
    return all_good

def check_environment_file():
    """Verifica se o arquivo .env está configurado"""
    print("⚙️ Verificando arquivo de configuração...")
    
    env_path = Path('.env')
    if not env_path.exists():
        print("   ❌ Arquivo .env não encontrado")
        return False
    
    # Lê o arquivo .env
    try:
        with open('.env', 'r') as f:
            content = f.read()
        
        # Verifica configurações críticas
        checks = {
            'AUDIO_DEVICE': 'auto' in content or 'plughw:' in content,
            'SPEECH_RECOGNITION_ENGINE': 'SPEECH_RECOGNITION_ENGINE=' in content,
            'SAMPLE_RATE': 'SAMPLE_RATE=' in content
        }
        
        all_configured = True
        for key, configured in checks.items():
            if configured:
                print(f"   ✅ {key}")
            else:
                print(f"   ❌ {key} (não configurado)")
                all_configured = False
        
        # Verifica se API está configurada
        api_configured = (
            'API_ENDPOINT=' in content and 
            'your-api-endpoint' not in content and
            'API_KEY=' in content and 
            'your_api_key' not in content
        )
        
        if api_configured:
            print("   ✅ API configurada")
        else:
            print("   ⚠️ API não configurada (opcional)")
        
        return all_configured
        
    except Exception as e:
        print(f"   ❌ Erro ao ler .env: {e}")
        return False

def check_python_dependencies():
    """Verifica se as dependências Python estão instaladas"""
    print("🐍 Verificando dependências Python...")
    
    required_modules = [
        'numpy',
        'pyaudio', 
        'speech_recognition',
        'requests',
        'flask',
        'dotenv'
    ]
    
    optional_modules = [
        'pocketsphinx',
        'vosk',
        'whisper',
        'faster_whisper'
    ]
    
    all_required = True
    
    # Verifica módulos obrigatórios
    for module in required_modules:
        try:
            __import__(module)
            print(f"   ✅ {module}")
        except ImportError:
            print(f"   ❌ {module} (obrigatório)")
            all_required = False
    
    # Verifica módulos opcionais
    optional_available = []
    for module in optional_modules:
        try:
            __import__(module)
            optional_available.append(module)
            print(f"   ✅ {module} (opcional)")
        except ImportError:
            print(f"   ⚠️ {module} (opcional, não instalado)")
    
    print(f"   📊 Engines opcionais disponíveis: {len(optional_available)}")
    return all_required

def check_directory_structure():
    """Verifica se a estrutura de diretórios está correta"""
    print("📁 Verificando estrutura de diretórios...")
    
    required_dirs = [
        'src/core',
        'src/transcription', 
        'src/api',
        'src/services',
        'scripts',
        'tests',
        'logs',
        'temp',
        'transcriptions'
    ]
    
    optional_dirs = [
        'models',
        'venv'
    ]
    
    all_present = True
    
    for directory in required_dirs:
        dir_path = Path(directory)
        if dir_path.exists() and dir_path.is_dir():
            print(f"   ✅ {directory}")
        else:
            print(f"   ❌ {directory} (obrigatório)")
            all_present = False
    
    for directory in optional_dirs:
        dir_path = Path(directory)
        if dir_path.exists() and dir_path.is_dir():
            print(f"   ✅ {directory} (opcional)")
        else:
            print(f"   ⚠️ {directory} (opcional, não encontrado)")
    
    return all_present

def run_quick_tests():
    """Executa testes rápidos dos componentes"""
    print("🧪 Executando testes rápidos...")
    
    test_results = {}
    
    # Teste de import dos módulos principais
    try:
        sys.path.append('src/core')
        sys.path.append('src/transcription')
        sys.path.append('src/api')
        
        from config import Config
        from speechRecognitionService import SpeechRecognitionService
        from apiService import ApiService
        
        print("   ✅ Imports dos módulos principais")
        test_results['imports'] = True
    except Exception as e:
        print(f"   ❌ Imports falharam: {e}")
        test_results['imports'] = False
    
    # Teste básico de configuração
    try:
        sample_rate = Config.AUDIO["sample_rate"]
        engine = Config.SPEECH_RECOGNITION["engine"]
        print(f"   ✅ Configuração carregada ({sample_rate}Hz, {engine})")
        test_results['config'] = True
    except Exception as e:
        print(f"   ❌ Configuração falhou: {e}")
        test_results['config'] = False
    
    # Teste de inicialização do speech service
    try:
        service = SpeechRecognitionService()
        engine_info = service.get_engine_info()
        print(f"   ✅ Speech service ({engine_info['engine']})")
        test_results['speech_service'] = True
    except Exception as e:
        print(f"   ❌ Speech service falhou: {e}")
        test_results['speech_service'] = False
    
    return test_results

def generate_report(results):
    """Gera relatório final da validação"""
    print("\n" + "=" * 60)
    print("📋 RELATÓRIO DE VALIDAÇÃO DA INSTALAÇÃO")
    print("=" * 60)
    
    # Componentes verificados
    components = {
        "Permissões de arquivos": results.get('permissions', False),
        "Arquivo de configuração": results.get('env_file', False), 
        "Dependências Python": results.get('dependencies', False),
        "Estrutura de diretórios": results.get('directories', False),
        "Testes básicos": results.get('quick_tests', {}).get('imports', False)
    }
    
    # Status geral
    all_critical_ok = all([
        results.get('permissions', False),
        results.get('env_file', False),
        results.get('dependencies', False),
        results.get('directories', False),
        results.get('quick_tests', {}).get('imports', False)
    ])
    
    print("\n🔍 STATUS DOS COMPONENTES:")
    for component, status in components.items():
        print(f"   {'✅' if status else '❌'} {component}")
    
    print(f"\n🎯 STATUS GERAL: {'✅ PRONTO PARA USO' if all_critical_ok else '❌ PROBLEMAS ENCONTRADOS'}")
    
    if all_critical_ok:
        print("\n🎉 INSTALAÇÃO VALIDADA COM SUCESSO!")
        print("\n📋 PRÓXIMOS PASSOS:")
        print("   1. Execute testes específicos:")
        print("      - python scripts/test_microphone_basic.py")
        print("      - python scripts/test_transcription_api.py") 
        print("      - python scripts/test_complete_system.py")
        print("   2. Configure API no .env (se necessário)")
        print("   3. Inicie o sistema: python src/mainWithServer.py")
        print("   4. Acesse: http://localhost:8000")
    else:
        print("\n⚠️ PROBLEMAS ENCONTRADOS QUE PRECISAM SER RESOLVIDOS:")
        
        if not results.get('permissions', False):
            print("   • Execute: chmod +x scripts/*.py scripts/*.sh")
        if not results.get('env_file', False):
            print("   • Configure o arquivo .env: cp .env.example .env")
        if not results.get('dependencies', False):
            print("   • Instale dependências: pip install -r requirements.txt")
        if not results.get('directories', False):
            print("   • Verifique estrutura de diretórios")
        if not results.get('quick_tests', {}).get('imports', False):
            print("   • Problemas nos imports - verifique instalação")
            
        print("\n💡 SUGESTÃO: Execute ./scripts/install_and_test.sh")
    
    return all_critical_ok

def main():
    """Função principal"""
    print("🔍 VALIDAÇÃO DA INSTALAÇÃO WHISPERSILENT")
    print("=" * 50)
    print()
    
    results = {}
    
    # Executa todas as verificações
    results['permissions'] = check_file_permissions()
    print()
    
    results['env_file'] = check_environment_file() 
    print()
    
    results['dependencies'] = check_python_dependencies()
    print()
    
    results['directories'] = check_directory_structure()
    print()
    
    results['quick_tests'] = run_quick_tests()
    print()
    
    # Gera relatório final
    success = generate_report(results)
    
    return success

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⏹️ Validação cancelada pelo usuário.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Erro inesperado na validação: {e}")
        sys.exit(1)