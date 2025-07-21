#!/usr/bin/env python3
"""
Teste de transcrição de API para WhisperSilent.
Testa se as APIs de transcrição estão funcionando corretamente.
"""

import sys
import os
import time
import numpy as np
import wave
import tempfile
from typing import Dict, List, Tuple

# Adiciona o diretório src ao path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src', 'core'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src', 'transcription'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src', 'api'))

class TranscriptionAPITester:
    """Classe para testar APIs de transcrição"""
    
    def __init__(self):
        """Inicializa o testador"""
        from speechRecognitionService import SpeechRecognitionService
        from apiService import ApiService
        from config import Config
        
        self.speech_service = SpeechRecognitionService()
        self.api_service = ApiService()
        self.config = Config
        
    def create_test_audio(self, frequency: float = 440.0, duration: float = 1.0) -> np.ndarray:
        """Cria áudio de teste (tom puro)"""
        sample_rate = self.config.AUDIO["sample_rate"]
        t = np.linspace(0, duration, int(sample_rate * duration))
        # Tom puro com amplitude baixa para não ser muito alto
        audio = (np.sin(2 * np.pi * frequency * t) * 0.1 * 32767).astype(np.int16)
        return audio
        
    def create_silence_audio(self, duration: float = 1.0) -> np.ndarray:
        """Cria áudio silencioso para teste"""
        sample_rate = self.config.AUDIO["sample_rate"]
        return np.zeros(int(sample_rate * duration), dtype=np.int16)
        
    def save_audio_to_wav(self, audio_data: np.ndarray, filename: str = None) -> str:
        """Salva áudio em arquivo WAV temporário"""
        if filename is None:
            fd, filename = tempfile.mkstemp(suffix='.wav')
            os.close(fd)
            
        sample_rate = self.config.AUDIO["sample_rate"]
        
        with wave.open(filename, 'wb') as wav_file:
            wav_file.setnchannels(1)  # Mono
            wav_file.setsampwidth(2)  # 16-bit
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(audio_data.tobytes())
            
        return filename
    
    def test_speech_recognition_engines(self) -> Dict:
        """Testa diferentes engines de reconhecimento de fala"""
        print("🔧 Testando engines de reconhecimento de fala...")
        
        results = {
            'engines_tested': [],
            'engines_working': [],
            'engines_failed': [],
            'test_results': {}
        }
        
        # Lista de engines para testar
        engines_to_test = [
            'google',      # Sempre disponível
            'sphinx',      # Offline
            'vosk',        # Offline  
            'whisper_local', # Offline
            'faster_whisper', # Offline
        ]
        
        # Cria áudio de teste (silêncio - mais previsível)
        test_audio = self.create_silence_audio(1.0)
        
        for engine in engines_to_test:
            print(f"   Testando engine: {engine}")
            results['engines_tested'].append(engine)
            
            try:
                # Configura engine
                if self.speech_service.switch_engine(engine):
                    # Testa transcrição
                    start_time = time.time()
                    result = self.speech_service.transcribe(test_audio)
                    end_time = time.time()
                    
                    processing_time = end_time - start_time
                    
                    # Armazena resultado
                    results['test_results'][engine] = {
                        'success': True,
                        'result': result,
                        'processing_time': processing_time,
                        'engine_info': self.speech_service.get_engine_info()
                    }
                    
                    results['engines_working'].append(engine)
                    print(f"      ✅ Sucesso ({processing_time:.2f}s): '{result}'")
                    
                else:
                    results['engines_failed'].append(engine)
                    results['test_results'][engine] = {
                        'success': False,
                        'error': 'Falha ao trocar para o engine'
                    }
                    print(f"      ❌ Falha ao trocar para {engine}")
                    
            except Exception as e:
                results['engines_failed'].append(engine)
                results['test_results'][engine] = {
                    'success': False,
                    'error': str(e)
                }
                print(f"      ❌ Erro em {engine}: {e}")
        
        print(f"   📊 Engines funcionando: {len(results['engines_working'])}/{len(results['engines_tested'])}")
        return results
    
    def test_api_service_connection(self) -> Dict:
        """Testa conexão com o serviço de API"""
        print("🌐 Testando conexão com API...")
        
        result = {
            'connection_available': False,
            'endpoint_configured': False,
            'api_key_configured': False,
            'test_send_success': False,
            'response_time': 0.0,
            'error': None
        }
        
        try:
            # Verifica configuração
            endpoint = self.config.API.get("endpoint", "")
            api_key = self.config.API.get("key", "")
            
            result['endpoint_configured'] = bool(endpoint and endpoint != "your_api_endpoint_here")
            result['api_key_configured'] = bool(api_key and api_key != "your_api_key_here")
            
            print(f"   Endpoint configurado: {'✅' if result['endpoint_configured'] else '❌'}")
            print(f"   API Key configurada: {'✅' if result['api_key_configured'] else '❌'}")
            
            if not (result['endpoint_configured'] and result['api_key_configured']):
                result['error'] = "API não configurada corretamente no .env"
                print("   ⚠️ Configure API_ENDPOINT e API_KEY no arquivo .env")
                return result
            
            # Testa envio de dados de exemplo
            test_data = {
                "text": "Teste de transcrição",
                "confidence": 0.95,
                "timestamp": time.time(),
                "engine": "test"
            }
            
            print("   Testando envio para API...")
            start_time = time.time()
            
            # Tenta enviar dados de teste
            success = self.api_service.send_transcription(test_data)
            
            end_time = time.time()
            result['response_time'] = end_time - start_time
            result['test_send_success'] = success
            result['connection_available'] = True
            
            if success:
                print(f"   ✅ Envio bem-sucedido ({result['response_time']:.2f}s)")
            else:
                print(f"   ❌ Falha no envio ({result['response_time']:.2f}s)")
                
        except Exception as e:
            result['error'] = str(e)
            print(f"   ❌ Erro na conexão: {e}")
        
        return result
    
    def test_end_to_end_transcription(self) -> Dict:
        """Teste end-to-end: captura → transcrição → API"""
        print("🔄 Testando fluxo completo (end-to-end)...")
        
        result = {
            'success': False,
            'steps_completed': [],
            'total_time': 0.0,
            'transcription_result': '',
            'api_sent': False,
            'error': None
        }
        
        try:
            start_time = time.time()
            
            # Passo 1: Gerar áudio de teste
            print("   1. Gerando áudio de teste...")
            test_audio = self.create_test_audio(frequency=440, duration=2.0)
            result['steps_completed'].append('audio_generation')
            
            # Passo 2: Transcrever áudio
            print("   2. Transcrevendo áudio...")
            # Usa o engine padrão configurado
            transcription = self.speech_service.transcribe(test_audio)
            result['transcription_result'] = transcription
            result['steps_completed'].append('transcription')
            print(f"      Resultado: '{transcription}'")
            
            # Passo 3: Enviar para API (se configurada)
            print("   3. Enviando para API...")
            if transcription:  # Só envia se teve resultado
                transcription_data = {
                    "text": transcription,
                    "confidence": 0.8,
                    "timestamp": time.time(),
                    "engine": self.speech_service.get_engine_info()['engine'],
                    "test": True
                }
                
                api_success = self.api_service.send_transcription(transcription_data)
                result['api_sent'] = api_success
                result['steps_completed'].append('api_sending')
                
                if api_success:
                    print("      ✅ Enviado para API")
                else:
                    print("      ⚠️ Falha no envio para API")
            else:
                print("      ⚠️ Sem resultado de transcrição para enviar")
            
            end_time = time.time()
            result['total_time'] = end_time - start_time
            result['success'] = len(result['steps_completed']) >= 2  # Pelo menos audio + transcription
            
            print(f"   ⏱️ Tempo total: {result['total_time']:.2f}s")
            
        except Exception as e:
            result['error'] = str(e)
            print(f"   ❌ Erro no teste end-to-end: {e}")
        
        return result
    
    def run_comprehensive_test(self) -> bool:
        """Executa todos os testes de API de transcrição"""
        print("=" * 60)
        print("🔬 TESTE ABRANGENTE DE TRANSCRIÇÃO E API")
        print("=" * 60)
        print()
        
        all_results = {}
        
        # Teste 1: Engines de reconhecimento
        engines_result = self.test_speech_recognition_engines()
        all_results['engines'] = engines_result
        print()
        
        # Teste 2: Conexão com API
        api_result = self.test_api_service_connection()
        all_results['api'] = api_result
        print()
        
        # Teste 3: Fluxo end-to-end
        e2e_result = self.test_end_to_end_transcription()
        all_results['end_to_end'] = e2e_result
        print()
        
        # Análise dos resultados
        print("=" * 60)
        print("📋 RESUMO DOS RESULTADOS")
        print("=" * 60)
        
        # Engines
        working_engines = len(engines_result['engines_working'])
        total_engines = len(engines_result['engines_tested'])
        print(f"🔧 Engines funcionando: {working_engines}/{total_engines}")
        if working_engines > 0:
            print(f"   ✅ Engines OK: {', '.join(engines_result['engines_working'])}")
        if engines_result['engines_failed']:
            print(f"   ❌ Engines com falha: {', '.join(engines_result['engines_failed'])}")
        
        # API
        api_ok = api_result['endpoint_configured'] and api_result['api_key_configured']
        print(f"🌐 API configurada: {'✅' if api_ok else '❌'}")
        if api_result['test_send_success']:
            print("   ✅ Teste de envio bem-sucedido")
        elif api_result['error']:
            print(f"   ❌ {api_result['error']}")
        
        # End-to-end
        print(f"🔄 Teste end-to-end: {'✅' if e2e_result['success'] else '❌'}")
        if e2e_result['transcription_result']:
            print(f"   Transcrição: '{e2e_result['transcription_result']}'")
        
        # Resultado final
        print()
        print("=" * 60)
        
        success_criteria = (
            working_engines > 0,  # Pelo menos um engine funciona
            e2e_result['success']  # Teste end-to-end passou
        )
        
        if all(success_criteria):
            print("🎉 TODOS OS TESTES CRÍTICOS PASSARAM!")
            print("   Sistema de transcrição está funcionando.")
            if not api_ok:
                print("   ⚠️ Configure a API no .env para funcionalidade completa.")
            return True
        else:
            print("❌ ALGUNS TESTES CRÍTICOS FALHARAM!")
            print("   Verifique as configurações e dependências.")
            return False


def main():
    """Função principal"""
    try:
        tester = TranscriptionAPITester()
        success = tester.run_comprehensive_test()
        
        print()
        if success:
            print("💡 PRÓXIMOS PASSOS:")
            print("   1. Sistema pronto para uso")
            print("   2. Inicie com: python src/mainWithServer.py")
            print("   3. Acesse: http://localhost:8000")
        else:
            print("💡 SUGESTÕES PARA RESOLVER PROBLEMAS:")
            print("   1. Configure API_ENDPOINT e API_KEY no .env")
            print("   2. Instale engines offline: pip install 'SpeechRecognition[pocketsphinx]'")
            print("   3. Verifique conexão com a internet para engines online")
            print("   4. Execute: python scripts/install_and_test.sh")
        
        return success
        
    except KeyboardInterrupt:
        print("\n⏹️ Teste cancelado pelo usuário.")
        return False
    except Exception as e:
        print(f"\n❌ Erro inesperado: {e}")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)