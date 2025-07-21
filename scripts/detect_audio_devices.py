#!/usr/bin/env python3
"""
Script utilitário para detectar e configurar dispositivos de áudio.
Pode ser usado de forma interativa ou automática.
"""

import sys
import os
import argparse

# Adiciona o diretório src ao path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src', 'core'))

from audioDeviceDetector import AudioDeviceDetector

def print_header():
    print("=" * 60)
    print("🎤 DETECTOR DE DISPOSITIVOS DE ÁUDIO - WhisperSilent")
    print("=" * 60)
    print()

def auto_detect_mode():
    """Modo de detecção automática"""
    print("🔍 Modo: Detecção Automática")
    print("-" * 30)
    
    detector = AudioDeviceDetector()
    
    # Mostra todos os dispositivos
    print("📋 Dispositivos disponíveis:")
    print(detector.list_all_devices())
    
    # Detecta automaticamente o melhor
    print("🤖 Executando detecção automática...")
    result = detector.auto_detect_best_device()
    
    if result:
        device_index, device_info = result
        print(f"✅ DISPOSITIVO RECOMENDADO:")
        print(f"   Índice: {device_index}")
        print(f"   Nome: {device_info['name']}")
        print(f"   Canais de entrada: {device_info['max_input_channels']}")
        print(f"   Taxa padrão: {device_info['default_samplerate']} Hz")
        print()
        print(f"💡 Para usar este dispositivo, configure:")
        print(f"   AUDIO_DEVICE={device_index}")
        print("   ou")
        print(f"   AUDIO_DEVICE=auto")
        return device_index
    else:
        print("❌ Nenhum dispositivo adequado foi encontrado automaticamente.")
        return None

def interactive_mode():
    """Modo interativo para seleção de dispositivo"""
    print("👤 Modo: Seleção Interativa")
    print("-" * 30)
    
    detector = AudioDeviceDetector()
    result = detector.interactive_device_selection()
    
    if result:
        device_index, device_info = result
        print()
        print(f"✅ DISPOSITIVO SELECIONADO:")
        print(f"   Índice: {device_index}")
        print(f"   Nome: {device_info['name']}")
        print()
        print(f"💡 Para usar este dispositivo, configure:")
        print(f"   AUDIO_DEVICE={device_index}")
        return device_index
    else:
        print("❌ Nenhum dispositivo foi selecionado.")
        return None

def list_mode():
    """Modo para apenas listar dispositivos"""
    print("📝 Modo: Listar Dispositivos")
    print("-" * 30)
    
    detector = AudioDeviceDetector()
    print(detector.list_all_devices())
    
    input_devices = detector.get_input_devices()
    if input_devices:
        print(f"💡 Dispositivos de entrada encontrados: {len(input_devices)}")
        print("   Para usar um dispositivo específico, configure AUDIO_DEVICE com:")
        print("   - 'auto' para detecção automática")
        print("   - Número do índice (ex: AUDIO_DEVICE=2)")
        print("   - Parte do nome (ex: AUDIO_DEVICE=USB)")
    else:
        print("❌ Nenhum dispositivo de entrada encontrado.")

def test_mode(device_index=None):
    """Modo de teste de dispositivo específico"""
    detector = AudioDeviceDetector()
    
    if device_index is None:
        print("🧪 Modo: Teste - Detectar e Testar Automaticamente")
        print("-" * 50)
        result = detector.auto_detect_best_device()
        if not result:
            print("❌ Nenhum dispositivo encontrado para teste.")
            return False
        device_index, device_info = result
        print(f"🎯 Testando dispositivo detectado: {device_info['name']}")
    else:
        print(f"🧪 Modo: Teste - Dispositivo {device_index}")
        print("-" * 30)
        try:
            device_info = detector.devices[device_index]
            print(f"🎯 Testando dispositivo: {device_info['name']}")
        except (IndexError, TypeError):
            print(f"❌ Dispositivo {device_index} não encontrado.")
            return False
    
    print("⏳ Testando captura de áudio por 3 segundos...")
    success = detector.test_device(device_index, duration=3.0)
    
    if success:
        print(f"✅ Teste bem-sucedido! Dispositivo {device_index} está funcionando.")
        return True
    else:
        print(f"❌ Teste falhou. Dispositivo {device_index} pode ter problemas.")
        return False

def update_env_file(device_index):
    """Atualiza o arquivo .env com o dispositivo selecionado"""
    env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
    
    if not os.path.exists(env_path):
        print(f"⚠️ Arquivo .env não encontrado em {env_path}")
        return False
    
    # Lê o arquivo atual
    with open(env_path, 'r') as f:
        lines = f.readlines()
    
    # Atualiza ou adiciona a linha AUDIO_DEVICE
    updated = False
    for i, line in enumerate(lines):
        if line.startswith('AUDIO_DEVICE='):
            lines[i] = f'AUDIO_DEVICE={device_index}\n'
            updated = True
            break
    
    if not updated:
        lines.append(f'AUDIO_DEVICE={device_index}\n')
    
    # Escreve o arquivo atualizado
    with open(env_path, 'w') as f:
        f.writelines(lines)
    
    print(f"✅ Arquivo .env atualizado: AUDIO_DEVICE={device_index}")
    return True

def main():
    parser = argparse.ArgumentParser(
        description="Detector de dispositivos de áudio para WhisperSilent",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos de uso:
  python detect_audio_devices.py --auto          # Detecção automática
  python detect_audio_devices.py --interactive   # Seleção interativa
  python detect_audio_devices.py --list          # Listar dispositivos
  python detect_audio_devices.py --test          # Testar dispositivo detectado
  python detect_audio_devices.py --test 2        # Testar dispositivo 2
  python detect_audio_devices.py --auto --update # Detectar e atualizar .env
        """
    )
    
    parser.add_argument('--auto', '-a', action='store_true',
                        help='Detectar automaticamente o melhor dispositivo')
    parser.add_argument('--interactive', '-i', action='store_true',
                        help='Seleção interativa de dispositivo')
    parser.add_argument('--list', '-l', action='store_true',
                        help='Listar todos os dispositivos disponíveis')
    parser.add_argument('--test', '-t', nargs='?', const=-1, type=int,
                        help='Testar dispositivo (sem argumento = auto, com número = específico)')
    parser.add_argument('--update', '-u', action='store_true',
                        help='Atualizar arquivo .env com dispositivo selecionado')
    
    args = parser.parse_args()
    
    # Se nenhum argumento foi fornecido, usa modo interativo
    if not any([args.auto, args.interactive, args.list, args.test is not None]):
        args.interactive = True
    
    print_header()
    
    device_index = None
    
    try:
        if args.list:
            list_mode()
        elif args.auto:
            device_index = auto_detect_mode()
        elif args.interactive:
            device_index = interactive_mode()
        elif args.test is not None:
            if args.test == -1:
                # Teste automático
                test_mode()
            else:
                # Teste de dispositivo específico
                test_mode(args.test)
        
        # Se --update foi especificado e temos um dispositivo, atualiza .env
        if args.update and device_index is not None:
            print()
            print("📝 Atualizando configuração...")
            update_env_file(device_index)
    
    except KeyboardInterrupt:
        print("\n\n⏹️ Operação cancelada pelo usuário.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Erro inesperado: {e}")
        sys.exit(1)
    
    print()
    print("🏁 Operação concluída.")

if __name__ == "__main__":
    main()