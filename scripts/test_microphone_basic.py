#!/usr/bin/env python3
"""
Teste básico e rápido de captura de microfone.
Versão simplificada para verificação inicial durante setup.
"""

import sys
import os
import time
import numpy as np

# Adiciona o diretório src ao path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src', 'core'))

def test_microphone_basic():
    """Teste básico e rápido do microfone"""
    print("🎤 Teste Básico de Microfone")
    print("=" * 40)
    
    try:
        from audioCapture import AudioCapture
        from config import Config
        
        # Teste 1: Verificar configuração
        print("1. Verificando configuração...")
        sample_rate = Config.AUDIO["sample_rate"]
        channels = Config.AUDIO["channels"]
        print(f"   ✅ Sample Rate: {sample_rate} Hz, Canais: {channels}")
        
        # Teste 2: Inicializar dispositivo
        print("2. Inicializando dispositivo de áudio...")
        audio_capture = AudioCapture()
        
        if not audio_capture.start():
            print("   ❌ Falha ao inicializar dispositivo")
            return False
        
        device_info = audio_capture.device_info
        print(f"   ✅ Dispositivo: {device_info['name']}")
        
        # Teste 3: Captura rápida (2 segundos)
        print("3. Testando captura (2s)... Fale alguma coisa!")
        
        samples_count = 0
        max_amplitude = 0.0
        start_time = time.time()
        
        while time.time() - start_time < 2.0:
            try:
                audio_data = audio_capture.q.get(timeout=0.1)
                if len(audio_data) > 0:
                    samples_count += len(audio_data)
                    amplitude = np.max(np.abs(audio_data))
                    max_amplitude = max(max_amplitude, amplitude)
            except:
                continue
        
        audio_capture.stop()
        
        # Resultados
        print(f"   📊 Amostras: {samples_count:,}")
        print(f"   🔊 Amplitude máxima: {max_amplitude:.6f}")
        
        if samples_count == 0:
            print("   ❌ Nenhuma amostra coletada")
            return False
        
        if max_amplitude < 1e-6:
            print("   ⚠️ Amplitude muito baixa - verifique o microfone")
            return False
        
        print("   ✅ Microfone funcionando!")
        return True
        
    except ImportError as e:
        print(f"   ❌ Módulo não encontrado: {e}")
        return False
    except Exception as e:
        print(f"   ❌ Erro: {e}")
        return False

def main():
    """Função principal"""
    if test_microphone_basic():
        print("\n🎉 SUCESSO: Microfone está capturando áudio!")
        return True
    else:
        print("\n❌ FALHA: Problemas na captura de áudio.")
        print("\nSoluções:")
        print("- Execute: python scripts/detect_audio_devices.py --auto")
        print("- Verifique se o microfone está conectado")
        print("- Teste com: arecord -l")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)