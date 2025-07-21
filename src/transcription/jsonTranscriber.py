import json
import numpy as np
import threading
import time
import os
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path

import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'core'))
from config import Config
from logger import log
from audioCapture import AudioCapture
from audioProcessor import AudioProcessor
from speechRecognitionService import SpeechRecognitionService

class JsonTranscriber:
    """
    Módulo independente para transcrição contínua com saída JSON.
    Captura áudio do microfone, transcreve usando engines disponíveis
    e mantém um JSON atualizado com as transcrições.
    """
    
    def __init__(self, output_file: str = "transcriptions.json"):
        self.output_file = Path(output_file)
        self.is_running = False
        self.transcriptions: List[Dict[str, Any]] = []
        self.stats = {
            "session_start": None,
            "total_transcriptions": 0,
            "total_audio_chunks": 0,
            "successful_transcriptions": 0,
            "empty_transcriptions": 0,
            "errors": 0,
            "engine_used": None,
            "last_update": None
        }
        
        # Inicializar componentes de áudio e transcrição
        self.audio_capture = AudioCapture()
        self.audio_processor = AudioProcessor(self.audio_capture.q)
        
        # Forçar uso da API do Google (testada e funcional)
        os.environ['SPEECH_RECOGNITION_ENGINE'] = 'google'
        self.speech_service = SpeechRecognitionService()
        
        # Threading
        self.processing_thread = None
        self.lock = threading.Lock()
        
        # Configurações
        self.min_chunk_duration = 2.0  # segundos mínimos para processar
        self.max_silence_duration = 3.0  # segundos de silêncio antes de processar
        
        # Carregar transcrições existentes se o arquivo existir
        self._load_existing_transcriptions()
        
        log.info(f"JsonTranscriber inicializado com engine: {self.speech_service.engine.value}")
        log.info(f"Arquivo de saída: {self.output_file.absolute()}")

    def _load_existing_transcriptions(self):
        """Carrega transcrições existentes do arquivo JSON"""
        try:
            if self.output_file.exists():
                with open(self.output_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.transcriptions = data.get('transcriptions', [])
                    self.stats.update(data.get('stats', {}))
                    log.info(f"Carregadas {len(self.transcriptions)} transcrições existentes")
        except Exception as e:
            log.warning(f"Erro ao carregar transcrições existentes: {e}")
            self.transcriptions = []

    def _save_transcriptions(self):
        """Salva as transcrições no arquivo JSON"""
        try:
            with self.lock:
                data = {
                    "metadata": {
                        "created_at": datetime.now().isoformat(),
                        "engine": self.speech_service.engine.value,
                        "language": self.speech_service.language,
                        "audio_config": {
                            "sample_rate": Config.AUDIO["sample_rate"],
                            "channels": Config.AUDIO["channels"],
                            "device": Config.AUDIO["device"]
                        }
                    },
                    "stats": self.stats,
                    "transcriptions": self.transcriptions
                }
                
                # Salvar atomicamente (escrever em arquivo temporário e renomear)
                temp_file = self.output_file.with_suffix('.tmp')
                with open(temp_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                
                temp_file.replace(self.output_file)
                
                self.stats["last_update"] = datetime.now().isoformat()
                
        except Exception as e:
            log.error(f"Erro ao salvar transcrições: {e}")

    def _add_transcription(self, text: str, audio_data: Dict[str, Any]):
        """Adiciona uma nova transcrição à lista"""
        transcription = {
            "id": len(self.transcriptions) + 1,
            "timestamp": datetime.now().isoformat(),
            "text": text,
            "confidence": audio_data.get("confidence", 0.0),
            "audio_info": {
                "duration_ms": audio_data.get("duration_ms", 0),
                "sample_count": audio_data.get("sample_count", 0),
                "max_amplitude": audio_data.get("max_amplitude", 0),
                "rms_amplitude": audio_data.get("rms_amplitude", 0)
            },
            "engine": self.speech_service.engine.value
        }
        
        with self.lock:
            self.transcriptions.append(transcription)
            self.stats["total_transcriptions"] += 1
            if text.strip():
                self.stats["successful_transcriptions"] += 1
            else:
                self.stats["empty_transcriptions"] += 1

    def _process_audio_chunk(self, audio_chunk: np.ndarray) -> Optional[str]:
        """Processa um chunk de áudio e retorna a transcrição"""
        try:
            # Calcular informações do áudio
            duration_ms = (len(audio_chunk) / Config.AUDIO["sample_rate"]) * 1000
            max_amplitude = float(np.max(np.abs(audio_chunk)))
            rms_amplitude = float(np.sqrt(np.mean(audio_chunk.astype(np.float64) ** 2)))
            
            audio_info = {
                "duration_ms": duration_ms,
                "sample_count": len(audio_chunk),
                "max_amplitude": max_amplitude,
                "rms_amplitude": rms_amplitude,
                "confidence": min(max_amplitude / 10000.0, 1.0)  # Estimativa simples de confiança
            }
            
            self.stats["total_audio_chunks"] += 1
            
            # Verificar se há atividade de voz suficiente
            if max_amplitude < 100:  # Threshold para ruído de fundo
                return None
            
            # Transcrever usando o serviço de speech recognition
            text = self.speech_service.transcribe(audio_chunk)
            
            # Adicionar transcrição (mesmo se vazia para estatísticas)
            self._add_transcription(text, audio_info)
            
            # Salvar imediatamente após cada transcrição
            self._save_transcriptions()
            
            return text if text.strip() else None
            
        except Exception as e:
            log.error(f"Erro ao processar chunk de áudio: {e}")
            self.stats["errors"] += 1
            return None

    def _audio_processing_loop(self):
        """Loop principal de processamento de áudio"""
        log.info("Iniciando loop de processamento de áudio...")
        
        try:
            # Iniciar captura de áudio
            audio_queue = self.audio_capture.start()
            
            # Buffer para acumular áudio
            audio_buffer = []
            last_process_time = time.time()
            silence_start = None
            
            print(f"🎤 [JSON TRANSCRIBER] Aguardando áudio...")
            
            while self.is_running:
                try:
                    # Obter chunk de áudio
                    chunk = audio_queue.get(timeout=0.1)
                    audio_buffer.append(chunk.flatten())
                    
                    current_time = time.time()
                    buffer_duration = len(np.concatenate(audio_buffer)) / Config.AUDIO["sample_rate"]
                    
                    # Verificar atividade de voz
                    chunk_amplitude = np.max(np.abs(chunk))
                    
                    if chunk_amplitude > 500:  # Há voz
                        silence_start = None
                        if buffer_duration >= self.min_chunk_duration:
                            # Processar buffer acumulado
                            combined_audio = np.concatenate(audio_buffer)
                            
                            print(f"\n🔄 [PROCESSING] {buffer_duration:.1f}s de áudio (amplitude: {chunk_amplitude:.0f})")
                            
                            text = self._process_audio_chunk(combined_audio)
                            
                            if text:
                                print(f"✅ [TRANSCRIBED] \"{text}\"")
                            else:
                                print(f"❌ [NO SPEECH] Nenhuma fala detectada")
                            
                            # Limpar buffer
                            audio_buffer = []
                            last_process_time = current_time
                    
                    else:  # Silêncio
                        if silence_start is None:
                            silence_start = current_time
                        elif (current_time - silence_start) > self.max_silence_duration and audio_buffer:
                            # Processar buffer antes do silêncio
                            if buffer_duration >= 1.0:  # Pelo menos 1 segundo
                                combined_audio = np.concatenate(audio_buffer)
                                
                                print(f"\n🔄 [SILENCE TRIGGER] Processando {buffer_duration:.1f}s antes do silêncio")
                                
                                text = self._process_audio_chunk(combined_audio)
                                
                                if text:
                                    print(f"✅ [TRANSCRIBED] \"{text}\"")
                            
                            # Limpar buffer
                            audio_buffer = []
                            silence_start = None
                            last_process_time = current_time
                    
                    # Forçar processamento se buffer muito grande (mais de 10 segundos)
                    if buffer_duration > 10.0:
                        combined_audio = np.concatenate(audio_buffer)
                        
                        print(f"\n🔄 [FORCE PROCESS] Buffer grande: {buffer_duration:.1f}s")
                        
                        text = self._process_audio_chunk(combined_audio)
                        
                        if text:
                            print(f"✅ [TRANSCRIBED] \"{text}\"")
                        
                        audio_buffer = []
                        last_process_time = current_time
                    
                except Exception as e:
                    if self.is_running:  # Só logar se ainda estiver rodando
                        log.debug(f"Timeout ou erro na fila de áudio: {e}")
                    continue
                    
        except Exception as e:
            log.error(f"Erro no loop de processamento: {e}")
            self.stats["errors"] += 1
        finally:
            # Processar qualquer áudio restante no buffer
            if audio_buffer:
                try:
                    combined_audio = np.concatenate(audio_buffer)
                    print(f"\n🔄 [FINAL PROCESS] Processando buffer final: {len(combined_audio)} samples")
                    text = self._process_audio_chunk(combined_audio)
                    if text:
                        print(f"✅ [FINAL TRANSCRIBED] \"{text}\"")
                except Exception as e:
                    log.error(f"Erro ao processar buffer final: {e}")
            
            # Parar captura de áudio
            self.audio_capture.stop()
            log.info("Loop de processamento de áudio finalizado")

    def start(self):
        """Inicia a transcrição contínua"""
        if self.is_running:
            log.warning("JsonTranscriber já está rodando")
            return
        
        self.is_running = True
        self.stats["session_start"] = datetime.now().isoformat()
        self.stats["engine_used"] = self.speech_service.engine.value
        
        # Iniciar thread de processamento
        self.processing_thread = threading.Thread(target=self._audio_processing_loop, daemon=True)
        self.processing_thread.start()
        
        print(f"🚀 [JSON TRANSCRIBER] Iniciado com engine: {self.speech_service.engine.value}")
        print(f"📄 [OUTPUT] Arquivo: {self.output_file.absolute()}")
        print(f"🎯 [CONFIG] Idioma: {self.speech_service.language}")
        
        log.info("JsonTranscriber iniciado com sucesso")

    def stop(self):
        """Para a transcrição contínua"""
        if not self.is_running:
            log.warning("JsonTranscriber não está rodando")
            return
        
        print(f"\n🛑 [JSON TRANSCRIBER] Parando...")
        
        self.is_running = False
        
        # Aguardar thread finalizar
        if self.processing_thread:
            self.processing_thread.join(timeout=5.0)
        
        # Salvar estado final
        self._save_transcriptions()
        
        # Exibir estatísticas finais
        print(f"\n📊 [ESTATÍSTICAS FINAIS]")
        print(f"   Total de chunks: {self.stats['total_audio_chunks']}")
        print(f"   Transcrições: {self.stats['successful_transcriptions']}")
        print(f"   Vazias: {self.stats['empty_transcriptions']}")
        print(f"   Erros: {self.stats['errors']}")
        print(f"   Arquivo: {self.output_file.absolute()}")
        
        log.info("JsonTranscriber parado com sucesso")

    def get_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas atuais"""
        with self.lock:
            return self.stats.copy()

    def get_transcriptions(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Retorna lista de transcrições"""
        with self.lock:
            if limit:
                return self.transcriptions[-limit:]
            return self.transcriptions.copy()

    def clear_transcriptions(self):
        """Limpa todas as transcrições"""
        with self.lock:
            self.transcriptions = []
            self.stats["total_transcriptions"] = 0
            self.stats["successful_transcriptions"] = 0
            self.stats["empty_transcriptions"] = 0
        
        self._save_transcriptions()
        log.info("Transcrições limpas")