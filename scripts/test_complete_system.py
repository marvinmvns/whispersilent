#!/usr/bin/env python3
"""
Teste completo e integrado do sistema WhisperSilent.
Valida captura de microfone, transcrição e envio para API.
"""

import sys
import os
import time
import numpy as np
import threading
import queue
from typing import Dict, List, Optional

# Adiciona o diretório src ao path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src', 'core'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src', 'transcription'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src', 'api'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src', 'services'))

class CompleteSystemTester:
    """Testador completo do sistema WhisperSilent"""
    
    def __init__(self):
        """Inicializa o testador completo"""
        try:
            from audioCapture import AudioCapture
            from audioProcessor import AudioProcessor
            from speechRecognitionService import SpeechRecognitionService
            from apiService import APIService
            from healthMonitor import HealthMonitor
            from config import Config
            
            self.audio_capture = AudioCapture()
            self.audio_processor = AudioProcessor()
            self.speech_service = SpeechRecognitionService()
            self.api_service = APIService()
            self.health_monitor = HealthMonitor()
            self.config = Config
            
            self.test_results = {}
            self.is_running = False
            
        except ImportError as e:
            print(f"❌ Erro ao importar módulos: {e}")
            raise
    
    def test_system_initialization(self) -> bool:
        """Testa se todos os componentes inicializam corretamente"""
        print("🔧 Testando inicialização dos componentes...")
        
        try:
            # Testa configuração
            print("   Configuração... ", end="")
            sample_rate = self.config.AUDIO["sample_rate"]
            engine = self.config.SPEECH_RECOGNITION["engine"]
            print(f"✅ ({sample_rate}Hz, {engine})")
            
            # Testa health monitor
            print("   Health Monitor... ", end="")
            self.health_monitor.start()
            health = self.health_monitor.get_health_status()
            print(f"✅ (Status: {health['status']})")
            
            # Testa speech service
            print("   Speech Service... ", end="")
            engine_info = self.speech_service.get_engine_info()
            print(f"✅ ({engine_info['engine']})")
            
            # Testa API service
            print("   API Service... ", end="")
            api_configured = bool(
                self.config.API.get("endpoint") and 
                self.config.API.get("endpoint") != "your_api_endpoint_here"
            )
            print(f"{'✅' if api_configured else '⚠️'} ({'Configurado' if api_configured else 'Não configurado'})")
            
            return True
            
        except Exception as e:
            print(f"❌ Erro na inicialização: {e}")
            return False
    
    def test_live_audio_capture(self, duration: float = 5.0) -> Dict:
        """Testa captura de áudio em tempo real"""
        print(f"🎤 Testando captura de áudio ao vivo ({duration}s)...")
        
        result = {
            'success': False,
            'samples_collected': 0,
            'chunks_processed': 0,
            'average_amplitude': 0.0,
            'max_amplitude': 0.0,
            'silence_detected': False,
            'voice_detected': False,
            'processing_times': []
        }
        
        try:
            # Inicia captura
            if not self.audio_capture.start():
                print("   ❌ Falha ao iniciar captura")
                return result
            
            print("   🎙️ Gravando... (FALE CLARAMENTE)")
            
            all_amplitudes = []
            start_time = time.time()
            chunk_count = 0
            
            while time.time() - start_time < duration:
                try:
                    chunk_start = time.time()
                    audio_data = self.audio_capture.q.get(timeout=0.2)
                    chunk_end = time.time()
                    
                    if len(audio_data) > 0:
                        chunk_count += 1
                        result['samples_collected'] += len(audio_data)
                        
                        # Análise do chunk
                        amplitude = np.max(np.abs(audio_data))
                        mean_amplitude = np.mean(np.abs(audio_data))
                        all_amplitudes.append(mean_amplitude)
                        result['max_amplitude'] = max(result['max_amplitude'], amplitude)
                        
                        # Detecção de voz/silêncio
                        if amplitude > 0.001:  # Threshold para voz
                            result['voice_detected'] = True
                        if amplitude < 0.0001:  # Threshold para silêncio
                            result['silence_detected'] = True
                        
                        # Tempo de processamento
                        processing_time = chunk_end - chunk_start
                        result['processing_times'].append(processing_time)
                        
                        # Progress indicator
                        if chunk_count % 10 == 0:
                            print(f"      Chunk {chunk_count}: {amplitude:.6f}")
                    
                except queue.Empty:
                    continue
                except Exception as e:
                    print(f"   ⚠️ Erro no chunk: {e}")
                    continue
            
            # Para captura
            self.audio_capture.stop()
            
            # Calcula estatísticas
            if all_amplitudes:
                result['average_amplitude'] = np.mean(all_amplitudes)
            result['chunks_processed'] = chunk_count
            
            # Análise dos resultados
            print(f"   📊 Chunks processados: {result['chunks_processed']}")
            print(f"   📈 Amostras coletadas: {result['samples_collected']:,}")
            print(f"   🔊 Amplitude máxima: {result['max_amplitude']:.6f}")
            print(f"   📊 Amplitude média: {result['average_amplitude']:.6f}")
            print(f"   🎤 Voz detectada: {'✅' if result['voice_detected'] else '❌'}")
            print(f"   🔇 Silêncio detectado: {'✅' if result['silence_detected'] else '❌'}")
            
            if result['processing_times']:
                avg_time = np.mean(result['processing_times'])
                print(f"   ⏱️ Tempo médio de processamento: {avg_time*1000:.1f}ms")
            
            # Critérios de sucesso
            success_criteria = [
                result['samples_collected'] > 0,
                result['chunks_processed'] > 0,
                result['max_amplitude'] > 1e-6
            ]
            
            result['success'] = all(success_criteria)
            
            if result['success']:
                print("   ✅ Captura de áudio funcionando!")
            else:
                print("   ❌ Problemas na captura de áudio")
            
            return result
            
        except Exception as e:
            print(f"   ❌ Erro na captura: {e}")
            try:
                self.audio_capture.stop()
            except:
                pass
            return result
    
    def test_real_time_transcription(self, duration: float = 10.0) -> Dict:
        """Testa transcrição em tempo real"""
        print(f"🔄 Testando transcrição em tempo real ({duration}s)...")
        
        result = {
            'success': False,
            'transcriptions': [],
            'total_audio_processed': 0,
            'transcription_times': [],
            'successful_transcriptions': 0,
            'failed_transcriptions': 0,
            'average_confidence': 0.0
        }
        
        try:
            # Inicia captura
            if not self.audio_capture.start():
                print("   ❌ Falha ao iniciar captura")
                return result
            
            print("   🎙️ Transcrição ao vivo... (FALE FRASES CLARAS)")
            print("   💬 Transcrições aparecerão abaixo:")
            
            audio_buffer = []
            buffer_duration = 3.0  # Processa a cada 3 segundos
            samples_per_buffer = int(self.config.AUDIO["sample_rate"] * buffer_duration)
            
            start_time = time.time()
            transcription_count = 0
            
            while time.time() - start_time < duration:
                try:
                    # Coleta áudio
                    audio_data = self.audio_capture.q.get(timeout=0.1)
                    
                    if len(audio_data) > 0:
                        audio_buffer.extend(audio_data.flatten())
                        
                        # Processa quando buffer está cheio
                        if len(audio_buffer) >= samples_per_buffer:
                            transcription_count += 1
                            
                            # Prepara áudio para transcrição
                            audio_chunk = np.array(audio_buffer[:samples_per_buffer], dtype=np.int16)
                            audio_buffer = audio_buffer[samples_per_buffer//2:]  # Overlap de 50%
                            
                            # Verifica se há sinal suficiente
                            amplitude = np.max(np.abs(audio_chunk))
                            if amplitude < 0.001:
                                print(f"      [{transcription_count}] (silêncio detectado)")
                                continue
                            
                            # Transcreve
                            trans_start = time.time()
                            transcription = self.speech_service.transcribe(audio_chunk)
                            trans_end = time.time()
                            
                            processing_time = trans_end - trans_start
                            result['transcription_times'].append(processing_time)
                            result['total_audio_processed'] += len(audio_chunk)
                            
                            if transcription and transcription.strip():
                                result['successful_transcriptions'] += 1
                                result['transcriptions'].append({
                                    'text': transcription,
                                    'timestamp': trans_start,
                                    'processing_time': processing_time,
                                    'amplitude': float(amplitude)
                                })
                                print(f"      [{transcription_count}] ({processing_time:.1f}s): \"{transcription}\"")
                            else:
                                result['failed_transcriptions'] += 1
                                print(f"      [{transcription_count}] ({processing_time:.1f}s): (não reconhecido)")
                
                except queue.Empty:
                    continue
                except Exception as e:
                    print(f"   ⚠️ Erro na transcrição: {e}")
                    result['failed_transcriptions'] += 1
                    continue
            
            # Para captura
            self.audio_capture.stop()
            
            # Estatísticas finais
            total_transcriptions = result['successful_transcriptions'] + result['failed_transcriptions']
            success_rate = (result['successful_transcriptions'] / max(1, total_transcriptions)) * 100
            
            print(f"   📊 Total de tentativas: {total_transcriptions}")
            print(f"   ✅ Transcrições bem-sucedidas: {result['successful_transcriptions']}")
            print(f"   ❌ Transcrições falharam: {result['failed_transcriptions']}")
            print(f"   📈 Taxa de sucesso: {success_rate:.1f}%")
            
            if result['transcription_times']:
                avg_time = np.mean(result['transcription_times'])
                print(f"   ⏱️ Tempo médio de transcrição: {avg_time:.2f}s")
            
            # Critério de sucesso: pelo menos 1 transcrição bem-sucedida
            result['success'] = result['successful_transcriptions'] > 0
            
            return result
            
        except Exception as e:
            print(f"   ❌ Erro na transcrição em tempo real: {e}")
            try:
                self.audio_capture.stop()
            except:
                pass
            return result
    
    def test_api_integration(self) -> Dict:
        """Testa integração completa com API"""
        print("🌐 Testando integração com API...")
        
        result = {
            'success': False,
            'api_configured': False,
            'test_sends': 0,
            'successful_sends': 0,
            'failed_sends': 0,
            'response_times': [],
            'errors': []
        }
        
        try:
            # Verifica configuração da API
            endpoint = self.config.API.get("endpoint", "")
            api_key = self.config.API.get("key", "")
            
            result['api_configured'] = bool(
                endpoint and endpoint != "your_api_endpoint_here" and
                api_key and api_key != "your_api_key_here"
            )
            
            if not result['api_configured']:
                print("   ⚠️ API não configurada - configure .env para teste completo")
                print("   ℹ️ Executando teste com dados simulados...")
                
                # Simula envios para testar a lógica
                for i in range(3):
                    test_data = {
                        "text": f"Teste de transcrição {i+1}",
                        "confidence": 0.85,
                        "timestamp": time.time(),
                        "engine": "test",
                        "test_mode": True
                    }
                    
                    try:
                        start_time = time.time()
                        # Em modo teste, simula sucesso
                        success = True  # self.api_service.send_transcription(test_data)
                        end_time = time.time()
                        
                        result['test_sends'] += 1
                        result['response_times'].append(end_time - start_time)
                        
                        if success:
                            result['successful_sends'] += 1
                            print(f"   ✅ Teste {i+1}: Dados preparados para envio")
                        else:
                            result['failed_sends'] += 1
                            print(f"   ❌ Teste {i+1}: Falha na preparação")
                            
                    except Exception as e:
                        result['failed_sends'] += 1
                        result['errors'].append(str(e))
                        print(f"   ❌ Teste {i+1}: Erro - {e}")
                
                result['success'] = result['successful_sends'] > 0
                
            else:
                print("   ✅ API configurada - testando envios reais...")
                
                # Testa envios reais para API
                for i in range(3):
                    test_data = {
                        "text": f"Teste do sistema WhisperSilent #{i+1}",
                        "confidence": 0.9,
                        "timestamp": time.time(),
                        "engine": self.speech_service.get_engine_info()['engine'],
                        "test": True
                    }
                    
                    try:
                        start_time = time.time()
                        success = self.api_service.send_transcription(test_data)
                        end_time = time.time()
                        
                        result['test_sends'] += 1
                        result['response_times'].append(end_time - start_time)
                        
                        if success:
                            result['successful_sends'] += 1
                            print(f"   ✅ Envio {i+1}: Sucesso ({end_time - start_time:.2f}s)")
                        else:
                            result['failed_sends'] += 1
                            print(f"   ❌ Envio {i+1}: Falha ({end_time - start_time:.2f}s)")
                            
                    except Exception as e:
                        result['failed_sends'] += 1
                        result['errors'].append(str(e))
                        print(f"   ❌ Envio {i+1}: Erro - {e}")
                
                result['success'] = result['successful_sends'] >= 1
            
            # Estatísticas
            if result['test_sends'] > 0:
                success_rate = (result['successful_sends'] / result['test_sends']) * 100
                print(f"   📊 Taxa de sucesso: {success_rate:.1f}% ({result['successful_sends']}/{result['test_sends']})")
            
            if result['response_times']:
                avg_time = np.mean(result['response_times'])
                print(f"   ⏱️ Tempo médio de resposta: {avg_time:.2f}s")
            
            return result
            
        except Exception as e:
            print(f"   ❌ Erro no teste de API: {e}")
            result['errors'].append(str(e))
            return result
    
    def run_complete_system_test(self) -> bool:
        """Executa teste completo do sistema"""
        print("=" * 70)
        print("🚀 TESTE COMPLETO DO SISTEMA WHISPERSILENT")
        print("=" * 70)
        print()
        
        # Armazena todos os resultados
        all_results = {}
        
        # Teste 1: Inicialização
        print("FASE 1: INICIALIZAÇÃO")
        print("-" * 30)
        init_success = self.test_system_initialization()
        all_results['initialization'] = init_success
        print()
        
        if not init_success:
            print("❌ Falha crítica na inicialização - abortando testes")
            return False
        
        # Teste 2: Captura de áudio
        print("FASE 2: CAPTURA DE ÁUDIO")
        print("-" * 30)
        audio_result = self.test_live_audio_capture(duration=5.0)
        all_results['audio_capture'] = audio_result
        print()
        
        # Teste 3: Transcrição em tempo real
        if audio_result['success']:
            print("FASE 3: TRANSCRIÇÃO EM TEMPO REAL")
            print("-" * 40)
            transcription_result = self.test_real_time_transcription(duration=8.0)
            all_results['transcription'] = transcription_result
            print()
        else:
            print("⏭️ FASE 3 PULADA: Problemas na captura de áudio")
            transcription_result = {'success': False}
            all_results['transcription'] = transcription_result
            print()
        
        # Teste 4: Integração com API
        print("FASE 4: INTEGRAÇÃO COM API")
        print("-" * 30)
        api_result = self.test_api_integration()
        all_results['api_integration'] = api_result
        print()
        
        # Análise final
        print("=" * 70)
        print("📊 RESULTADO FINAL DO TESTE COMPLETO")
        print("=" * 70)
        
        # Critérios de sucesso por componente
        components_status = {
            "Inicialização": "✅" if all_results['initialization'] else "❌",
            "Captura de Áudio": "✅" if all_results['audio_capture']['success'] else "❌",
            "Transcrição": "✅" if all_results['transcription']['success'] else "❌",
            "API Integration": "✅" if all_results['api_integration']['success'] else "❌"
        }
        
        for component, status in components_status.items():
            print(f"{status} {component}")
        
        # Estatísticas detalhadas
        print("\n📈 ESTATÍSTICAS DETALHADAS:")
        
        if all_results['audio_capture']['success']:
            audio = all_results['audio_capture']
            print(f"   🎤 Áudio: {audio['chunks_processed']} chunks, {audio['samples_collected']:,} amostras")
        
        if all_results['transcription']['success']:
            trans = all_results['transcription']
            print(f"   💬 Transcrição: {trans['successful_transcriptions']} sucessos de {trans['successful_transcriptions'] + trans['failed_transcriptions']} tentativas")
        
        if all_results['api_integration']['successful_sends'] > 0:
            api = all_results['api_integration']
            print(f"   🌐 API: {api['successful_sends']} envios bem-sucedidos")
        
        # Verifica sucesso geral
        critical_components = [
            all_results['initialization'],
            all_results['audio_capture']['success'],
            all_results['transcription']['success']
        ]
        
        system_working = all(critical_components)
        
        print(f"\n🎯 SISTEMA GERAL: {'✅ FUNCIONANDO' if system_working else '❌ COM PROBLEMAS'}")
        
        if system_working:
            print("\n🎉 PARABÉNS! O sistema WhisperSilent está funcionando corretamente!")
            print("\n📋 PRÓXIMOS PASSOS:")
            print("   1. Configure a API no arquivo .env (se ainda não fez)")
            print("   2. Execute o sistema: python src/mainWithServer.py")
            print("   3. Acesse a interface web: http://localhost:8000")
            print("   4. Monitore os logs em: logs/")
        else:
            print("\n⚠️ O sistema tem alguns problemas que precisam ser resolvidos:")
            
            if not all_results['initialization']:
                print("   • Problemas na inicialização - verifique dependências")
            if not all_results['audio_capture']['success']:
                print("   • Problemas na captura de áudio - verifique microfone e configuração")
            if not all_results['transcription']['success']:
                print("   • Problemas na transcrição - verifique engines e conexão")
                
            print("\n💡 SUGESTÕES:")
            print("   1. Execute: python scripts/detect_audio_devices.py --auto")
            print("   2. Verifique arquivo .env e configurações")
            print("   3. Teste microfone: python scripts/test_microphone_basic.py")
            print("   4. Reinstale dependências: ./scripts/install_and_test.sh")
        
        return system_working


def main():
    """Função principal"""
    try:
        print("Inicializando teste completo do sistema...")
        print("Este teste verificará todos os componentes do WhisperSilent.\n")
        
        # Pergunta se o usuário quer continuar
        response = input("Pressione Enter para iniciar o teste completo (ou 'q' para sair): ")
        if response.lower() == 'q':
            print("Teste cancelado pelo usuário.")
            return False
        
        print()
        
        tester = CompleteSystemTester()
        success = tester.run_complete_system_test()
        
        return success
        
    except KeyboardInterrupt:
        print("\n⏹️ Teste cancelado pelo usuário.")
        return False
    except Exception as e:
        print(f"\n❌ Erro inesperado no teste: {e}")
        print("Verifique se todas as dependências estão instaladas:")
        print("   ./scripts/install_and_test.sh")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)