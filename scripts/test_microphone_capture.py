#!/usr/bin/env python3
"""
Teste básico de captura de microfone para WhisperSilent.
Este script testa se o microfone está funcionando corretamente.
"""

import sys
import os
import time
import numpy as np
from typing import Optional, Tuple, Dict

# Adiciona o diretório src ao path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src', 'core'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src', 'transcription'))

from audioCapture import AudioCapture
from audioDeviceDetector import AudioDeviceDetector
from config import Config


class MicrophoneTester:
    """Classe para testar a captura de microfone"""
    
    def __init__(self):
        self.audio_capture = AudioCapture()
        self.detector = AudioDeviceDetector()
        
    def test_device_detection(self) -> bool:
        """Testa se a detecção de dispositivos está funcionando"""
        print("🔍 Testando detecção de dispositivos de áudio...")
        
        try:
            devices = self.detector.get_input_devices()
            if not devices:
                print("❌ Nenhum dispositivo de entrada encontrado")
                return False
            
            print(f"✅ {len(devices)} dispositivo(s) de entrada encontrado(s)")
            
            # Lista os dispositivos encontrados
            for idx, device in devices.items():
                print(f"   [{idx}] {device['name']} - {device['max_input_channels']} canais")
            
            return True
            
        except Exception as e:
            print(f"❌ Erro na detecção de dispositivos: {e}")
            return False
    
    def test_audio_configuration(self) -> bool:
        """Testa se a configuração de áudio está válida"""
        print("⚙️ Testando configuração de áudio...")
        
        try:
            # Verifica configuração básica
            sample_rate = Config.AUDIO["sample_rate"]
            channels = Config.AUDIO["channels"]
            chunk_duration = Config.AUDIO["chunk_duration_ms"]
            
            print(f"   Sample Rate: {sample_rate} Hz")
            print(f"   Canais: {channels}")
            print(f"   Duração do chunk: {chunk_duration} ms")
            
            # Valida valores
            if sample_rate <= 0 or sample_rate > 192000:
                print(f"❌ Sample rate inválido: {sample_rate}")
                return False
            
            if channels not in [1, 2]:
                print(f"❌ Número de canais inválido: {channels}")
                return False
            
            if chunk_duration <= 0 or chunk_duration > 10000:
                print(f"❌ Duração do chunk inválida: {chunk_duration}")
                return False
            
            print("✅ Configuração de áudio válida")
            return True
            
        except Exception as e:
            print(f"❌ Erro na configuração de áudio: {e}")
            return False
    
    def test_device_initialization(self) -> bool:
        """Testa se o dispositivo de áudio pode ser inicializado"""
        print("🎤 Testando inicialização do dispositivo de áudio...")
        
        try:
            # Tenta inicializar o dispositivo
            if not self.audio_capture.start():
                print("❌ Falha ao inicializar dispositivo de áudio")
                return False
            
            # Verifica se o dispositivo foi configurado corretamente
            if self.audio_capture.device_info is None:
                print("❌ Informações do dispositivo não disponíveis")
                return False
            
            device_info = self.audio_capture.device_info
            print(f"✅ Dispositivo inicializado: {device_info['name']}")
            print(f"   Taxa de amostragem: {device_info['default_samplerate']} Hz")
            print(f"   Canais de entrada: {device_info['max_input_channels']}")
            
            # Para o dispositivo
            self.audio_capture.stop()
            return True
            
        except Exception as e:
            print(f"❌ Erro na inicialização do dispositivo: {e}")
            try:
                self.audio_capture.stop()
            except:
                pass
            return False
    
    def test_audio_capture_basic(self, duration: float = 3.0) -> bool:
        """Testa captura básica de áudio"""
        print(f"📊 Testando captura de áudio por {duration} segundos...")
        
        try:
            # Inicia captura
            if not self.audio_capture.start():
                print("❌ Falha ao iniciar captura")
                return False
            
            print("   🎙️ Gravando... (fale alguma coisa)")
            
            samples_collected = 0
            max_amplitude = 0.0
            start_time = time.time()
            
            # Coleta dados por alguns segundos
            while time.time() - start_time < duration:
                try:
                    # Pega dados da fila com timeout
                    audio_data = self.audio_capture.q.get(timeout=0.1)
                    
                    # Analisa os dados
                    if len(audio_data) > 0:
                        samples_collected += len(audio_data)
                        amplitude = np.max(np.abs(audio_data))
                        max_amplitude = max(max_amplitude, amplitude)
                    
                except:
                    # Timeout é normal, continua
                    continue
            
            # Para a captura
            self.audio_capture.stop()
            
            # Analisa resultados
            print(f"   📈 Amostras coletadas: {samples_collected}")
            print(f"   🔊 Amplitude máxima: {max_amplitude:.6f}")
            
            if samples_collected == 0:
                print("❌ Nenhuma amostra de áudio foi coletada")
                return False
            
            if max_amplitude < 1e-6:
                print("⚠️ Amplitude muito baixa - microfone pode estar mudo ou com problema")
                return False
            
            print("✅ Captura de áudio funcionando")
            return True
            
        except Exception as e:
            print(f"❌ Erro na captura de áudio: {e}")
            try:
                self.audio_capture.stop()
            except:
                pass
            return False
    
    def test_signal_analysis(self, duration: float = 5.0) -> Dict:
        """Testa análise avançada do sinal de áudio"""
        print(f"🔬 Testando análise de sinal por {duration} segundos...")
        
        results = {
            'success': False,
            'samples_total': 0,
            'amplitude_max': 0.0,
            'amplitude_mean': 0.0,
            'silence_ratio': 0.0,
            'frequency_peak': 0.0
        }
        
        try:
            if not self.audio_capture.start():
                print("❌ Falha ao iniciar captura para análise")
                return results
            
            print("   🎙️ Analisando áudio... (fale claramente)")
            
            all_samples = []
            start_time = time.time()
            
            # Coleta todos os dados
            while time.time() - start_time < duration:
                try:
                    audio_data = self.audio_capture.q.get(timeout=0.1)
                    if len(audio_data) > 0:
                        # Converte para mono se necessário
                        if len(audio_data.shape) > 1:
                            audio_data = np.mean(audio_data, axis=1)
                        all_samples.extend(audio_data.flatten())
                except:
                    continue
            
            self.audio_capture.stop()
            
            if not all_samples:
                print("❌ Nenhuma amostra coletada para análise")
                return results
            
            # Converte para numpy array
            audio_array = np.array(all_samples, dtype=np.float32)
            
            # Análise básica
            results['samples_total'] = len(audio_array)
            results['amplitude_max'] = float(np.max(np.abs(audio_array)))
            results['amplitude_mean'] = float(np.mean(np.abs(audio_array)))
            
            # Análise de silêncio (threshold baseado na amplitude média)
            silence_threshold = max(results['amplitude_mean'] * 0.1, 1e-4)
            silence_samples = np.sum(np.abs(audio_array) < silence_threshold)
            results['silence_ratio'] = silence_samples / len(audio_array)
            
            # Análise de frequência (FFT simples)
            try:
                fft = np.fft.fft(audio_array)
                freqs = np.fft.fftfreq(len(audio_array), 1/Config.AUDIO["sample_rate"])
                # Pega apenas frequências positivas
                positive_freqs = freqs[:len(freqs)//2]
                positive_fft = np.abs(fft[:len(fft)//2])
                # Encontra pico de frequência
                peak_idx = np.argmax(positive_fft)
                results['frequency_peak'] = float(positive_freqs[peak_idx])
            except:
                results['frequency_peak'] = 0.0
            
            # Exibe resultados
            print(f"   📊 Amostras analisadas: {results['samples_total']:,}")
            print(f"   🔊 Amplitude máxima: {results['amplitude_max']:.6f}")
            print(f"   📈 Amplitude média: {results['amplitude_mean']:.6f}")
            print(f"   🔇 Taxa de silêncio: {results['silence_ratio']:.1%}")
            print(f"   🎵 Pico de frequência: {results['frequency_peak']:.1f} Hz")
            
            # Avaliação da qualidade
            if results['amplitude_max'] < 1e-5:
                print("⚠️ Sinal muito fraco - verifique se o microfone está funcionando")
            elif results['silence_ratio'] > 0.95:
                print("⚠️ Muito silêncio detectado - fale mais próximo ao microfone")
            elif results['amplitude_mean'] > 0.1:
                print("⚠️ Sinal muito alto - verifique o volume do microfone")
            else:
                print("✅ Qualidade do sinal adequada")
            
            results['success'] = True
            return results
            
        except Exception as e:
            print(f"❌ Erro na análise de sinal: {e}")
            try:
                self.audio_capture.stop()
            except:
                pass
            return results
    
    def run_comprehensive_test(self) -> bool:
        """Executa todos os testes de captura de microfone"""
        print("=" * 60)
        print("🎤 TESTE ABRANGENTE DE CAPTURA DE MICROFONE")
        print("=" * 60)
        print()
        
        tests_passed = 0
        total_tests = 5
        
        # Teste 1: Detecção de dispositivos
        if self.test_device_detection():
            tests_passed += 1
        print()
        
        # Teste 2: Configuração
        if self.test_audio_configuration():
            tests_passed += 1
        print()
        
        # Teste 3: Inicialização do dispositivo
        if self.test_device_initialization():
            tests_passed += 1
        print()
        
        # Teste 4: Captura básica
        if self.test_audio_capture_basic():
            tests_passed += 1
        print()
        
        # Teste 5: Análise de sinal
        signal_results = self.test_signal_analysis()
        if signal_results['success']:
            tests_passed += 1
        print()
        
        # Resultado final
        print("=" * 60)
        print(f"📋 RESULTADO DOS TESTES: {tests_passed}/{total_tests} APROVADOS")
        print("=" * 60)
        
        if tests_passed == total_tests:
            print("🎉 TODOS OS TESTES PASSARAM! Microfone está funcionando corretamente.")
            return True
        elif tests_passed >= 3:
            print("⚠️ A maioria dos testes passou, mas há algumas questões a resolver.")
            return False
        else:
            print("❌ MUITOS TESTES FALHARAM! Verifique a configuração do microfone.")
            return False


def main():
    """Função principal"""
    try:
        tester = MicrophoneTester()
        success = tester.run_comprehensive_test()
        
        print()
        if success:
            print("💡 PRÓXIMOS PASSOS:")
            print("   1. Execute o teste de transcrição de API")
            print("   2. Inicie o sistema principal: python src/mainWithServer.py")
        else:
            print("💡 SUGESTÕES PARA RESOLVER PROBLEMAS:")
            print("   1. Verifique se o microfone está conectado")
            print("   2. Execute: python scripts/detect_audio_devices.py --auto")
            print("   3. Teste dispositivos manualmente com arecord -l")
            print("   4. Verifique as configurações no arquivo .env")
        
        return success
        
    except KeyboardInterrupt:
        print("\n⏹️ Teste cancelado pelo usuário.")
        return False
    except Exception as e:
        print(f"\n❌ Erro inesperado: {e}")
        return False


if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)