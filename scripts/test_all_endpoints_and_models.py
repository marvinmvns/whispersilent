#!/usr/bin/env python3
"""
Comprehensive test script for all transcription endpoints and offline models
Tests all available speech recognition engines with different audio inputs
"""

import sys
import os
import time
import numpy as np
import sounddevice as sd
import speech_recognition as sr
from typing import List, Dict, Optional, Tuple, Any
import json
import threading
import queue
from datetime import datetime

# Add src directories to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src', 'core'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src', 'transcription'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src', 'api'))

from audioDeviceDetector import AudioDeviceDetector
from speechRecognitionService import SpeechRecognitionService, TranscriptionEngine
from config import Config
from logger import log

class ComprehensiveTranscriptionTester:
    """Comprehensive tester for all transcription engines and models"""
    
    def __init__(self):
        self.device_detector = AudioDeviceDetector()
        self.recognizer = sr.Recognizer()
        self.recording_duration = 5.0  # seconds
        self.sample_rate = 16000
        self.channels = 1
        
        # Test results storage
        self.test_results = {
            'timestamp': datetime.now().isoformat(),
            'engines_tested': [],
            'successful_engines': [],
            'failed_engines': [],
            'microphone_results': [],
            'performance_metrics': {}
        }
        
        # Get available engines
        self.available_engines = list(TranscriptionEngine)
        
        print("🔍 Detectando motores de transcrição disponíveis...")
        self._check_engine_availability()
    
    def _check_engine_availability(self):
        """Check which engines are available based on dependencies and configuration"""
        self.engine_status = {}
        
        for engine in self.available_engines:
            status = {
                'available': False,
                'reason': '',
                'requires_config': False,
                'offline': False,
                'config_keys': []
            }
            
            try:
                if engine == TranscriptionEngine.GOOGLE:
                    # Always available - no API key required
                    status['available'] = True
                    status['reason'] = 'Gratuito - sem API key necessária'
                
                elif engine == TranscriptionEngine.GOOGLE_CLOUD:
                    status['requires_config'] = True
                    status['config_keys'] = ['GOOGLE_CLOUD_CREDENTIALS_JSON']
                    # Check if credentials are available
                    if Config.SPEECH_RECOGNITION.get('google_cloud_credentials'):
                        status['available'] = True
                        status['reason'] = 'Credenciais configuradas'
                    else:
                        status['reason'] = 'Credenciais Google Cloud não configuradas'
                
                elif engine == TranscriptionEngine.SPHINX:
                    status['offline'] = True
                    try:
                        import pocketsphinx
                        status['available'] = True
                        status['reason'] = 'Biblioteca pocketsphinx disponível'
                    except ImportError:
                        status['reason'] = 'Biblioteca pocketsphinx não instalada'
                
                elif engine == TranscriptionEngine.WIT:
                    status['requires_config'] = True
                    status['config_keys'] = ['WIT_AI_KEY']
                    if Config.SPEECH_RECOGNITION.get('wit_key'):
                        status['available'] = True
                        status['reason'] = 'API key configurada'
                    else:
                        status['reason'] = 'WIT_AI_KEY não configurada'
                
                elif engine == TranscriptionEngine.AZURE:
                    status['requires_config'] = True
                    status['config_keys'] = ['AZURE_SPEECH_KEY', 'AZURE_SPEECH_LOCATION']
                    if Config.SPEECH_RECOGNITION.get('azure_key'):
                        status['available'] = True
                        status['reason'] = 'API key configurada'
                    else:
                        status['reason'] = 'AZURE_SPEECH_KEY não configurada'
                
                elif engine == TranscriptionEngine.HOUNDIFY:
                    status['requires_config'] = True
                    status['config_keys'] = ['HOUNDIFY_CLIENT_ID', 'HOUNDIFY_CLIENT_KEY']
                    if Config.SPEECH_RECOGNITION.get('houndify_client_id'):
                        status['available'] = True
                        status['reason'] = 'Credenciais configuradas'
                    else:
                        status['reason'] = 'Credenciais Houndify não configuradas'
                
                elif engine == TranscriptionEngine.IBM:
                    status['requires_config'] = True
                    status['config_keys'] = ['IBM_SPEECH_USERNAME', 'IBM_SPEECH_PASSWORD']
                    if Config.SPEECH_RECOGNITION.get('ibm_username'):
                        status['available'] = True
                        status['reason'] = 'Credenciais configuradas'
                    else:
                        status['reason'] = 'Credenciais IBM não configuradas'
                
                elif engine == TranscriptionEngine.WHISPER_LOCAL:
                    status['offline'] = True
                    try:
                        import whisper
                        status['available'] = True
                        status['reason'] = 'Biblioteca whisper disponível'
                    except ImportError:
                        status['reason'] = 'Biblioteca openai-whisper não instalada'
                
                elif engine == TranscriptionEngine.WHISPER_API:
                    status['requires_config'] = True
                    status['config_keys'] = ['OPENAI_API_KEY']
                    if Config.SPEECH_RECOGNITION.get('openai_api_key'):
                        status['available'] = True
                        status['reason'] = 'API key configurada'
                    else:
                        status['reason'] = 'OPENAI_API_KEY não configurada'
                
                elif engine == TranscriptionEngine.FASTER_WHISPER:
                    status['offline'] = True
                    try:
                        import faster_whisper
                        status['available'] = True
                        status['reason'] = 'Biblioteca faster-whisper disponível'
                    except ImportError:
                        status['reason'] = 'Biblioteca faster-whisper não instalada'
                
                elif engine == TranscriptionEngine.GROQ:
                    status['requires_config'] = True
                    status['config_keys'] = ['GROQ_API_KEY']
                    if Config.SPEECH_RECOGNITION.get('groq_api_key'):
                        status['available'] = True
                        status['reason'] = 'API key configurada'
                    else:
                        status['reason'] = 'GROQ_API_KEY não configurada'
                
                elif engine == TranscriptionEngine.VOSK:
                    status['offline'] = True
                    status['requires_config'] = True
                    status['config_keys'] = ['VOSK_MODEL_PATH']
                    try:
                        import vosk
                        model_path = Config.SPEECH_RECOGNITION.get('vosk_model_path')
                        if model_path and os.path.exists(model_path):
                            status['available'] = True
                            status['reason'] = 'Biblioteca vosk e modelo disponíveis'
                        else:
                            status['reason'] = 'Modelo Vosk não encontrado'
                    except ImportError:
                        status['reason'] = 'Biblioteca vosk não instalada'
                
                elif engine == TranscriptionEngine.CUSTOM_ENDPOINT:
                    status['requires_config'] = True
                    status['config_keys'] = ['CUSTOM_SPEECH_ENDPOINT']
                    if Config.SPEECH_RECOGNITION.get('custom_endpoint'):
                        status['available'] = True
                        status['reason'] = 'Endpoint customizado configurado'
                    else:
                        status['reason'] = 'CUSTOM_SPEECH_ENDPOINT não configurado'
                
            except Exception as e:
                status['reason'] = f'Erro na verificação: {str(e)}'
            
            self.engine_status[engine] = status
    
    def print_engine_status(self):
        """Print status of all engines"""
        print("\n🔧 STATUS DOS MOTORES DE TRANSCRIÇÃO")
        print("=" * 80)
        
        available_count = sum(1 for status in self.engine_status.values() if status['available'])
        total_count = len(self.engine_status)
        
        print(f"📊 Motores disponíveis: {available_count}/{total_count}")
        print()
        
        # Group engines by type
        online_engines = []
        offline_engines = []
        unavailable_engines = []
        
        for engine, status in self.engine_status.items():
            if status['available']:
                if status['offline']:
                    offline_engines.append((engine, status))
                else:
                    online_engines.append((engine, status))
            else:
                unavailable_engines.append((engine, status))
        
        # Print available online engines
        if online_engines:
            print("🌐 MOTORES ONLINE DISPONÍVEIS:")
            for engine, status in online_engines:
                config_info = \" (\" + \", \".join(status['config_keys']) + \")\" if status['config_keys'] else \"\"\
                print(f\"   ✅ {engine.value.upper()}{config_info}\")
                print(f\"      💡 {status['reason']}\")
            print()
        
        # Print available offline engines
        if offline_engines:
            print("💾 MOTORES OFFLINE DISPONÍVEIS:")
            for engine, status in offline_engines:
                config_info = \" (\" + \", \".join(status['config_keys']) + \")\" if status['config_keys'] else \"\"\
                print(f\"   ✅ {engine.value.upper()}{config_info}\")
                print(f\"      💡 {status['reason']}\")
            print()
        
        # Print unavailable engines
        if unavailable_engines:
            print("❌ MOTORES NÃO DISPONÍVEIS:")
            for engine, status in unavailable_engines:
                config_info = \" (\" + \", \".join(status['config_keys']) + \")\" if status['config_keys'] else \"\"\
                print(f\"   🔴 {engine.value.upper()}{config_info}\")
                print(f\"      ❌ {status['reason']}\")
            print()
    
    def test_all_available_engines(self):
        """Test all available engines with microphone input"""
        print(\"\\n🎤 TESTE DE TRANSCRIÇÃO COM TODOS OS MOTORES DISPONÍVEIS\")
        print(\"=\" * 80)
        
        # Get best microphone
        recommended_device = self.device_detector.get_recommended_device()
        if not recommended_device:
            print(\"❌ Nenhum microfone disponível!\")
            return
        
        device_index, device_info = recommended_device
        print(f\"🎯 Usando microfone: {device_info['name']} (índice: {device_index})\")
        print(f\"⏱️ Duração da gravação: {self.recording_duration} segundos por motor\")
        print(\"🗣️ Fale algo durante cada gravação para testar a transcrição\")
        print(\"=\" * 80)
        
        available_engines = [(engine, status) for engine, status in self.engine_status.items() 
                           if status['available']]
        
        if not available_engines:
            print(\"❌ Nenhum motor de transcrição disponível!\")
            return
        
        print(f\"\\n📝 Testando {len(available_engines)} motores disponíveis...\")
        
        for i, (engine, status) in enumerate(available_engines):
            print(f\"\\n--- Teste {i+1}/{len(available_engines)} ---\")
            print(f\"🔧 Motor: {engine.value.upper()}\")
            print(f\"🌐 Tipo: {'Offline' if status['offline'] else 'Online'}\")
            print(f\"⚙️ Configuração: {status['reason']}\")
            
            try:
                print(f\"\\n⏳ Gravando áudio... (gravando por {self.recording_duration}s)\")
                print(\"🗣️ FALE AGORA!\")
                
                # Record audio
                audio_data = self._record_audio(device_index)
                if audio_data is None:
                    print(\"❌ Falha na captura de áudio\")
                    self._record_test_result(engine, False, \"Falha na captura de áudio\", 0, None)
                    continue
                
                # Analyze signal
                signal_stats = self._analyze_audio_signal(audio_data)
                print(f\"📊 Amplitude máxima: {signal_stats['max_amplitude']:.2f}\")
                
                # Test transcription with this engine
                print(f\"🔄 Transcrevendo com {engine.value}...\")
                
                start_time = time.time()
                transcription = self._test_engine_transcription(engine, audio_data)
                processing_time = (time.time() - start_time) * 1000  # Convert to ms
                
                if transcription:
                    print(f\"✅ Transcrição ({processing_time:.2f}ms): \\\"{transcription}\\\"\")
                    self._record_test_result(engine, True, transcription, processing_time, signal_stats)
                else:
                    print(\"🔇 Nenhuma fala detectada ou transcrição vazia\")
                    self._record_test_result(engine, False, \"Transcrição vazia\", processing_time, signal_stats)
                
            except Exception as e:
                error_msg = str(e)
                print(f\"❌ Erro durante o teste: {error_msg}\")
                self._record_test_result(engine, False, error_msg, 0, None)
            
            print(\"-\" * 50)
            
            # Small pause between tests
            if i < len(available_engines) - 1:
                print(\"⏸️ Pausa de 2 segundos antes do próximo teste...\")
                time.sleep(2)
        
        # Print final summary
        self._print_comprehensive_summary()
    
    def _test_engine_transcription(self, engine: TranscriptionEngine, audio_data: np.ndarray) -> str:
        \"\"\"Test transcription with a specific engine\"\"\"
        # Create a speech recognition service with this specific engine
        original_engine = Config.SPEECH_RECOGNITION.get(\"engine\", \"google\")
        
        # Temporarily change config to use this engine
        Config.SPEECH_RECOGNITION[\"engine\"] = engine.value
        
        try:
            # Create service with new engine
            service = SpeechRecognitionService()
            
            # Perform transcription
            result = service.transcribe(audio_data)
            return result
            
        finally:
            # Restore original engine
            Config.SPEECH_RECOGNITION[\"engine\"] = original_engine
    
    def _record_audio(self, device_index: int) -> Optional[np.ndarray]:
        \"\"\"Record audio from specific device\"\"\"
        try:
            recording = sd.rec(
                int(self.recording_duration * self.sample_rate),
                samplerate=self.sample_rate,
                channels=self.channels,
                device=device_index,
                dtype='int16'
            )
            sd.wait()
            return recording.flatten()
        except Exception as e:
            log.error(f\"Error recording from device {device_index}: {e}\")
            return None
    
    def _analyze_audio_signal(self, audio_data: np.ndarray) -> Dict:
        \"\"\"Analyze audio signal properties\"\"\"
        stats = {
            'max_amplitude': float(np.max(np.abs(audio_data))),
            'rms': float(np.sqrt(np.mean(audio_data.astype(np.float64) ** 2))),
            'variance': float(np.var(audio_data.astype(np.float64))),
            'energy': float(np.sum(audio_data.astype(np.float64) ** 2))
        }
        return stats
    
    def _record_test_result(self, engine: TranscriptionEngine, success: bool, 
                          result: str, processing_time: float, signal_stats: Optional[Dict]):
        \"\"\"Record test result for later analysis\"\"\"
        test_result = {
            'engine': engine.value,
            'success': success,
            'result': result,
            'processing_time_ms': processing_time,
            'signal_stats': signal_stats,
            'timestamp': datetime.now().isoformat(),
            'offline': self.engine_status[engine]['offline']
        }
        
        self.test_results['engines_tested'].append(test_result)
        
        if success:
            self.test_results['successful_engines'].append(engine.value)
        else:
            self.test_results['failed_engines'].append({
                'engine': engine.value,
                'reason': result
            })
    
    def _print_comprehensive_summary(self):
        \"\"\"Print comprehensive test summary\"\"\"
        print(\"\\n\" + \"=\" * 80)
        print(\"📋 RESUMO ABRANGENTE DOS TESTES\")
        print(\"=\" * 80)
        
        total_tested = len(self.test_results['engines_tested'])
        successful = len(self.test_results['successful_engines'])
        failed = len(self.test_results['failed_engines'])
        
        print(f\"📊 Estatísticas Gerais:\")
        print(f\"   🔧 Motores testados: {total_tested}\")
        print(f\"   ✅ Sucessos: {successful}\")
        print(f\"   ❌ Falhas: {failed}\")
        print(f\"   📈 Taxa de sucesso: {(successful/total_tested*100):.1f}%\" if total_tested > 0 else \"   📈 Taxa de sucesso: 0%\")
        
        # Successful engines
        if self.test_results['successful_engines']:
            print(f\"\\n🎉 MOTORES COM TRANSCRIÇÃO BEM-SUCEDIDA:\")
            
            successful_results = [r for r in self.test_results['engines_tested'] if r['success']]
            
            # Sort by processing time
            successful_results.sort(key=lambda x: x['processing_time_ms'])
            
            for result in successful_results:
                engine_type = \"💾 Offline\" if result['offline'] else \"🌐 Online\"
                print(f\"   ✅ {result['engine'].upper()} ({engine_type})\")
                print(f\"      💬 Transcrição: \\\"{result['result']}\\\"\")
                print(f\"      ⚡ Tempo: {result['processing_time_ms']:.2f}ms\")
                if result['signal_stats']:
                    print(f\"      📊 Amplitude: {result['signal_stats']['max_amplitude']:.2f}\")
                print()
            
            # Performance analysis
            print(\"⚡ ANÁLISE DE PERFORMANCE:\")
            avg_time = np.mean([r['processing_time_ms'] for r in successful_results])
            fastest = min(successful_results, key=lambda x: x['processing_time_ms'])
            slowest = max(successful_results, key=lambda x: x['processing_time_ms'])
            
            print(f\"   📊 Tempo médio: {avg_time:.2f}ms\")
            print(f\"   🏃 Mais rápido: {fastest['engine']} ({fastest['processing_time_ms']:.2f}ms)\")
            print(f\"   🐌 Mais lento: {slowest['engine']} ({slowest['processing_time_ms']:.2f}ms)\")
            print()
        
        # Failed engines
        if self.test_results['failed_engines']:
            print(\"⚠️ MOTORES COM FALHAS:\")
            for failure in self.test_results['failed_engines']:
                print(f\"   🔴 {failure['engine'].upper()}\")
                print(f\"      ❌ Motivo: {failure['reason']}\")
            print()
        
        # Configuration recommendations
        print(\"💡 RECOMENDAÇÕES DE CONFIGURAÇÃO:\")
        
        if successful_results:
            # Recommend fastest offline engine
            offline_engines = [r for r in successful_results if r['offline']]
            if offline_engines:
                best_offline = min(offline_engines, key=lambda x: x['processing_time_ms'])
                print(f\"   💾 Melhor motor offline: {best_offline['engine']} ({best_offline['processing_time_ms']:.2f}ms)\")
            
            # Recommend fastest online engine
            online_engines = [r for r in successful_results if not r['offline']]
            if online_engines:
                best_online = min(online_engines, key=lambda x: x['processing_time_ms'])
                print(f\"   🌐 Melhor motor online: {best_online['engine']} ({best_online['processing_time_ms']:.2f}ms)\")
            
            # Overall recommendation
            best_overall = fastest
            print(f\"   🏆 Recomendação geral: {best_overall['engine']}\")
            print(f\"   📝 Para usar: SPEECH_RECOGNITION_ENGINE={best_overall['engine']} no .env\")
        
        print()
        print(\"🔧 PRÓXIMOS PASSOS:\")
        print(\"   1. Configure o motor recomendado no seu arquivo .env\")
        print(\"   2. Para motores que falharam, verifique as dependências necessárias\")
        print(\"   3. Execute o sistema principal: python3 src/mainWithServer.py\")
        print(\"   4. Teste a transcrição em tempo real\")
        print(\"=\" * 80)
    
    def save_results_to_file(self, filename: Optional[str] = None):
        \"\"\"Save test results to JSON file\"\"\"
        if not filename:
            timestamp = datetime.now().strftime(\"%Y%m%d_%H%M%S\")
            filename = f\"transcription_test_results_{timestamp}.json\"
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.test_results, f, indent=2, ensure_ascii=False)
            print(f\"📄 Resultados salvos em: {filename}\")
        except Exception as e:
            print(f\"❌ Erro ao salvar resultados: {e}\")
    
    def test_installation_requirements(self):
        \"\"\"Test installation requirements for each engine\"\"\"
        print(\"\\n🔍 TESTE DE REQUISITOS DE INSTALAÇÃO\")
        print(\"=\" * 60)
        
        requirements = {
            'speech_recognition': 'SpeechRecognition',
            'sounddevice': 'sounddevice',
            'numpy': 'numpy',
            'pocketsphinx': 'pocketsphinx (para Sphinx)',
            'whisper': 'openai-whisper (para Whisper Local)',
            'faster_whisper': 'faster-whisper (para Faster Whisper)',
            'vosk': 'vosk (para Vosk)',
        }
        
        for module, description in requirements.items():
            try:
                __import__(module)
                print(f\"✅ {description}\")
            except ImportError:
                print(f\"❌ {description} - não instalado\")
        
        print()

def main():
    \"\"\"Main function\"\"\"
    try:
        print(\"🚀 TESTE ABRANGENTE DE MOTORES DE TRANSCRIÇÃO\")
        print(\"=\" * 80)
        print(\"Este script testa todos os motores de transcrição disponíveis\")
        print(\"incluindo modelos offline e endpoints online.\")
        print(\"=\" * 80)
        
        # Create tester
        tester = ComprehensiveTranscriptionTester()
        
        # Show installation requirements
        tester.test_installation_requirements()
        
        # Show engine status
        tester.print_engine_status()
        
        # Ask user if they want to proceed with microphone tests
        available_engines = [engine for engine, status in tester.engine_status.items() if status['available']]
        
        if not available_engines:
            print(\"\\n❌ Nenhum motor de transcrição disponível para teste!\")
            print(\"💡 Configure as variáveis de ambiente necessárias ou instale as dependências.\")
            return
        
        print(f\"\\n🎤 {len(available_engines)} motores disponíveis para teste com microfone.\")
        
        response = input(\"\\n🤔 Deseja prosseguir com os testes de microfone? (s/N): \").strip().lower()
        
        if response in ['s', 'sim', 'y', 'yes']:
            tester.test_all_available_engines()
            
            # Ask if user wants to save results
            save_response = input(\"\\n💾 Deseja salvar os resultados em arquivo JSON? (s/N): \").strip().lower()
            if save_response in ['s', 'sim', 'y', 'yes']:
                tester.save_results_to_file()
        else:
            print(\"\\n⏹️ Testes de microfone cancelados pelo usuário.\")
            print(\"💡 Execute novamente quando quiser testar com microfone.\")
        
    except KeyboardInterrupt:
        print(\"\\n\\n⏹️ Teste cancelado pelo usuário\")
    except Exception as e:
        print(f\"\\n❌ Erro durante o teste: {e}\")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()