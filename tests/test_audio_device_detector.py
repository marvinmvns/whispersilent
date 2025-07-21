#!/usr/bin/env python3
"""
Teste para o módulo AudioDeviceDetector
"""

import sys
import os
import unittest
from unittest.mock import Mock, patch

# Adiciona o caminho do src
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src', 'core'))

from audioDeviceDetector import AudioDeviceDetector

class TestAudioDeviceDetector(unittest.TestCase):
    
    def setUp(self):
        """Configuração inicial para cada teste"""
        self.detector = AudioDeviceDetector()
    
    @patch('sounddevice.query_devices')
    def test_device_detection(self, mock_query_devices):
        """Testa se os dispositivos são detectados corretamente"""
        # Mock dos dispositivos de exemplo
        mock_devices = [
            {
                'name': 'Built-in Output',
                'max_input_channels': 0,
                'max_output_channels': 2,
                'default_samplerate': 44100
            },
            {
                'name': 'USB Microphone',
                'max_input_channels': 1,
                'max_output_channels': 0,
                'default_samplerate': 48000
            },
            {
                'name': 'seeed-voicecard',
                'max_input_channels': 2,
                'max_output_channels': 2,
                'default_samplerate': 48000
            }
        ]
        
        mock_query_devices.return_value = mock_devices
        
        # Atualiza dispositivos
        self.detector._refresh_devices()
        
        # Verifica se encontrou dispositivos de entrada
        input_devices = self.detector.get_input_devices()
        self.assertEqual(len(input_devices), 2)  # USB Mic e Seeed
    
    def test_microphone_detection(self):
        """Testa identificação de microfones"""
        # Dispositivo que é claramente um microfone
        mic_device = {
            'name': 'USB Microphone',
            'max_input_channels': 1,
            'max_output_channels': 0
        }
        
        self.assertTrue(self.detector.is_microphone_device(mic_device))
        
        # Dispositivo que não é microfone
        speaker_device = {
            'name': 'Built-in Output Speaker',
            'max_input_channels': 0,
            'max_output_channels': 2
        }
        
        self.assertFalse(self.detector.is_microphone_device(speaker_device))
    
    def test_device_scoring(self):
        """Testa o sistema de pontuação de dispositivos"""
        # Dispositivo de alta prioridade (Seeed)
        seeed_device = {
            'name': 'seeed-voicecard',
            'max_input_channels': 2,
            'max_output_channels': 2
        }
        
        # Dispositivo genérico
        generic_device = {
            'name': 'Generic Audio Device',
            'max_input_channels': 1,
            'max_output_channels': 0
        }
        
        seeed_score = self.detector.score_device_priority(seeed_device)
        generic_score = self.detector.score_device_priority(generic_device)
        
        # Seeed deve ter pontuação maior
        self.assertGreater(seeed_score, generic_score)
    
    def test_list_all_devices(self):
        """Testa a listagem de dispositivos"""
        # Testa se retorna uma string não vazia
        device_list = self.detector.list_all_devices()
        self.assertIsInstance(device_list, str)
        self.assertIn("Dispositivos de áudio", device_list)

def run_live_test():
    """Executa teste em tempo real com dispositivos reais"""
    print("=" * 60)
    print("🧪 TESTE EM TEMPO REAL - DETECTOR DE DISPOSITIVOS")
    print("=" * 60)
    
    detector = AudioDeviceDetector()
    
    print("📋 1. Listando todos os dispositivos:")
    print(detector.list_all_devices())
    
    print("\n🔍 2. Detectando dispositivos de entrada:")
    input_devices = detector.get_input_devices()
    print(f"Encontrados {len(input_devices)} dispositivos de entrada")
    
    for device in input_devices:
        is_mic = detector.is_microphone_device(device['info'])
        score = detector.score_device_priority(device['info'])
        print(f"  - Índice {device['index']}: {device['info']['name']}")
        print(f"    Microfone: {'Sim' if is_mic else 'Não'}, Pontuação: {score}")
    
    print("\n🤖 3. Testando detecção automática:")
    recommended = detector.get_recommended_device()
    if recommended:
        device_index, device_info = recommended
        print(f"✅ Dispositivo recomendado:")
        print(f"   Índice: {device_index}")
        print(f"   Nome: {device_info['name']}")
        print(f"   Canais: {device_info['max_input_channels']}")
    else:
        print("❌ Nenhum dispositivo recomendado encontrado")
    
    print("\n🧪 4. Testando dispositivo recomendado:")
    if recommended:
        device_index, device_info = recommended
        print(f"Testando dispositivo {device_index} por 2 segundos...")
        success = detector.test_device(device_index, duration=2.0)
        if success:
            print("✅ Teste de captura bem-sucedido!")
        else:
            print("❌ Teste de captura falhou")
    
    print("\n" + "=" * 60)
    print("🏁 Teste concluído")

if __name__ == "__main__":
    # Executa testes unitários
    print("Executando testes unitários...")
    unittest.main(argv=[''], exit=False, verbosity=2)
    
    print("\n" * 2)
    
    # Executa teste em tempo real
    try:
        run_live_test()
    except KeyboardInterrupt:
        print("\n\n⏹️ Teste cancelado pelo usuário.")
    except Exception as e:
        print(f"\n❌ Erro no teste em tempo real: {e}")