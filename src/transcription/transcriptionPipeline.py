import threading
import time
import queue
import sys
import os

# Add parent directories to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'core'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'services'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'api'))

from audioCapture import AudioCapture
from audioProcessor import AudioProcessor
from speechRecognitionService import SpeechRecognitionService
from googleTranscribeService import GoogleTranscribeService
from apiService import ApiService
from config import Config
from healthMonitor import HealthMonitor
from transcriptionStorage import TranscriptionStorage
from transcriptionFiles import TranscriptionFileManager
from logger import log

class TranscriptionPipeline:
    def __init__(self):
        self.audio_queue = queue.Queue() # Queue for raw audio data from AudioCapture
        self.processed_audio_queue = queue.Queue() # Queue for processed audio chunks from AudioProcessor
        
        self.audio_capture = AudioCapture()
        self.audio_processor = AudioProcessor(self.audio_queue) # AudioProcessor consumes from audio_queue
        
        # Choose transcription service based on configuration
        # Priority: SpeechRecognition > Google Transcribe > fallback
        speech_engine = Config.SPEECH_RECOGNITION.get("engine", "").lower()
        
        if speech_engine and speech_engine != "disabled":
            self.transcription_service = SpeechRecognitionService()
            log.info(f"Using SpeechRecognition Service with {speech_engine} engine")
        elif Config.GOOGLE_TRANSCRIBE["enabled"]:
            self.transcription_service = GoogleTranscribeService()
            log.info("Using Google Transcribe Service for transcription")
        else:
            log.error("No transcription service configured! Please set SPEECH_RECOGNITION_ENGINE or enable GOOGLE_TRANSCRIBE")
            raise ValueError("No transcription service available")
            
        self.api_service = ApiService()
        self.health_monitor = HealthMonitor(self)
        self.transcription_storage = TranscriptionStorage()
        self.file_manager = TranscriptionFileManager()
        
        self.is_running = False
        self.processing_thread = None
        self.api_sending_enabled = True  # Toggle for proactive API sending

    def _processing_loop(self):
        log.info('Iniciando loop de processamento de áudio...')
        chunk_count = 0
        try:
            # AudioCapture puts data into self.audio_queue
            # AudioProcessor consumes from self.audio_queue and yields processed chunks
            for audio_chunk in self.audio_processor.process_audio():
                if not self.is_running: # Check if pipeline is stopped
                    break
                
                if audio_chunk is not None and audio_chunk.size > 0:
                    chunk_count += 1
                    duration_seconds = audio_chunk.size / Config.AUDIO["sample_rate"]
                    print(f"🔊 [AUDIO #{chunk_count:04d}] Chunk detectado: {audio_chunk.size} samples ({duration_seconds:.2f}s) - Processando...")
                    log.info(f"Chunk #{chunk_count}: {audio_chunk.size} samples, {duration_seconds:.2f}s duration")
                    
                    self.health_monitor.record_chunk_processed()
                    self.processed_audio_queue.put(audio_chunk)
                    self._process_chunk_from_queue() # Process immediately or in another thread
                else:
                    # Log periodic status even when no audio is detected
                    if chunk_count % 50 == 0:  # Every 50 iterations without audio
                        print(f"⏳ [STATUS] Aguardando áudio... ({chunk_count} iterações)")

        except Exception as e:
            log.error(f"Erro crítico no loop de processamento de áudio: {e}")
            print(f"🚨 [ERRO CRÍTICO] Loop de processamento falhou: {e}")
        finally:
            log.info('Loop de processamento de áudio finalizado.')
            print(f"🏁 [PIPELINE] Loop finalizado - Total de chunks processados: {chunk_count}")
            self.is_running = False # Ensure state is updated on exit

    def _process_chunk_from_queue(self):
        # This method can be called directly or from a separate thread if parallel processing is desired
        # For simplicity, processing sequentially here as in the JS version's queue logic
        if not self.processed_audio_queue.empty():
            chunk = self.processed_audio_queue.get()
            self._process_audio_chunk(chunk)

    def _process_audio_chunk(self, audio_chunk):
        try:
            start_time = time.time()
            chunk_duration = audio_chunk.size / Config.AUDIO["sample_rate"]
            
            # Transcrever áudio
            print(f"⚙️  [PROCESSING] Iniciando transcr. engine: {getattr(self.transcription_service, 'engine', 'unknown')}")
            log.info(f'Processando chunk de áudio ({audio_chunk.size} samples, {chunk_duration:.2f}s)...')
            
            transcription = self.transcription_service.transcribe(audio_chunk)
            processing_time_ms = (time.time() - start_time) * 1000
            
            if transcription and transcription.strip():
                words_count = len(transcription.split())
                chars_count = len(transcription)
                
                # Enhanced transcription output
                print(f"📝 [TRANSCRIÇÃO] ✅ Sucesso em {processing_time_ms:.0f}ms")
                print(f"    📊 Texto: \"{transcription}\" ({words_count} palavras, {chars_count} chars)")
                print(f"    ⏱️  Performance: {chunk_duration:.2f}s áudio → {processing_time_ms:.0f}ms processamento")
                
                log.info(f'Transcrição obtida em {processing_time_ms:.2f}ms: "{transcription}"')
                
                # Record successful transcription
                self.health_monitor.record_transcription_success(processing_time_ms)
                
                # Store transcription
                api_sent = False
                record_id = self.transcription_storage.add_transcription(
                    text=transcription,
                    processing_time_ms=processing_time_ms,
                    chunk_size=audio_chunk.size,
                    api_sent=False
                )
                
                # Enhanced storage logging
                total_transcriptions = len(self.transcription_storage.transcriptions)
                print(f"💾 [STORAGE] ✅ Salvo ID: {record_id} (Total: {total_transcriptions} transcrições)")
                
                # Create detailed record for file storage
                transcription_record = {
                    "id": record_id,
                    "text": transcription,
                    "timestamp": time.time(),
                    "processing_time_ms": processing_time_ms,
                    "chunk_size": audio_chunk.size,
                    "chunk_duration_s": chunk_duration,
                    "words_count": words_count,
                    "chars_count": chars_count,
                    "api_sent": False
                }
                
                # Save to daily JSON file
                json_file_path = self.file_manager.append_to_daily_file(transcription_record)
                print(f"📄 [JSON] Salvo em: {os.path.basename(json_file_path)}")
                
                # Send to API only if enabled
                if self.api_sending_enabled:
                    try:
                        api_endpoint = os.getenv('API_ENDPOINT', 'não configurado')
                        print(f"🌐 [API] Enviando para: {api_endpoint}")
                        
                        self.health_monitor.record_api_request_sent()
                        # Determine service type for API metadata
                        if hasattr(self.transcription_service, 'engine'):
                            service_type = f"speech-recognition-{self.transcription_service.engine.value}"
                        elif Config.GOOGLE_TRANSCRIBE["enabled"]:
                            service_type = "google-transcribe"
                        else:
                            service_type = "unknown"
                            
                        self.api_service.send_transcription(transcription, {
                            "chunkSize": audio_chunk.size,
                            "chunkDurationS": chunk_duration,
                            "processingTimeMs": processing_time_ms,
                            "recordId": record_id,
                            "transcriptionService": service_type,
                            "wordsCount": words_count,
                            "charsCount": chars_count
                        })
                        
                        # Mark as sent in storage
                        self.transcription_storage.mark_api_sent(record_id)
                        transcription_record["api_sent"] = True
                        api_sent = True
                        
                        print(f"✅ [API] ✅ Enviado com sucesso (ID: {record_id})")
                        log.info(f"API request successful for transcription {record_id}")
                        
                    except Exception as api_error:
                        print(f"🚨 [API] ❌ Erro: {str(api_error)[:100]}...")
                        self.health_monitor.record_api_request_failed(str(api_error))
                        log.error(f"Failed to send transcription to API: {api_error}")
                        # Don't raise - continue processing other chunks
                else:
                    print(f"⏸️  [API] Envio desabilitado - salvo apenas localmente")
                    log.debug("API sending disabled - transcription stored locally only")
                    
                # Summary line
                status_icon = "✅" if api_sent else "💾"
                print(f"{status_icon} [RESUMO] ID:{record_id} | {words_count}w | {processing_time_ms:.0f}ms | {'API+Local' if api_sent else 'Local'}")
                print(f"{'─'*80}")
                
            else:
                processing_time_ms = (time.time() - start_time) * 1000
                print(f"🔇 [SILÊNCIO] Nenhuma fala detectada ({processing_time_ms:.0f}ms processamento)")
                log.debug(f'Nenhuma fala detectada no chunk (processado em {processing_time_ms:.2f}ms)')
                
        except Exception as e:
            processing_time_ms = (time.time() - start_time) * 1000
            print(f"🚨 [ERRO] Falha ao processar chunk: {str(e)[:100]}... ({processing_time_ms:.0f}ms)")
            log.error(f'Erro ao processar chunk: {e}', exc_info=True)
            self.health_monitor.record_transcription_failure(str(e))
            # Continue processing next chunks even if an error occurs

    def start(self):
        if self.is_running:
            log.info("Pipeline já está em execução.")
            return

        try:
            print(f"\n🚀 [PIPELINE] Iniciando sistema de transcrição...")
            print(f"🎯 [CONFIG] Engine: {getattr(self.transcription_service, 'engine', 'unknown')}")
            print(f"🔧 [CONFIG] API sending: {'habilitado' if self.api_sending_enabled else 'desabilitado'}")
            log.info('Iniciando pipeline de transcrição...')
            
            # Start audio capture in its own thread if it blocks
            # For sounddevice, the callback runs in a separate thread, so start() itself is non-blocking
            self.audio_capture.start() # This starts the sounddevice stream and populates self.audio_queue
            self.is_running = True

            # Start the processing loop in a separate thread
            self.processing_thread = threading.Thread(target=self._processing_loop, daemon=True)
            self.processing_thread.start()

            print(f"✅ [PIPELINE] Sistema iniciado com sucesso!")
            print(f"🎤 [STATUS] Aguardando áudio... Fale no microfone!")
            print(f"{'='*60}")
            log.info('Pipeline de transcrição iniciado com sucesso')
            log.info('Aguardando áudio... Fale no microfone!')
        except Exception as e:
            print(f"🚨 [ERRO] Falha ao iniciar pipeline: {e}")
            log.error(f'Erro ao iniciar pipeline: {e}')
            self.stop() # Ensure cleanup if start fails
            raise

    def stop(self):
        if self.is_running:
            print(f"\n🛑 [PIPELINE] Parando sistema de transcrição...")
            log.info('Parando pipeline de transcrição...')
            self.is_running = False
            
            # Stop audio capture
            self.audio_capture.stop()
            
            # Signal AudioProcessor to stop by putting None into its input queue
            # This assumes AudioProcessor.process_audio() checks for None
            self.audio_queue.put(None)

            # Wait for the processing thread to finish
            if self.processing_thread and self.processing_thread.is_alive():
                self.processing_thread.join(timeout=5) # Wait up to 5 seconds
                if self.processing_thread.is_alive():
                    log.warning("Processing thread did not terminate gracefully.")

            # Limpar arquivos temporários
            self.transcription_service.cleanup()
            
            print(f"✅ [PIPELINE] Sistema parado com sucesso")
            log.info('Pipeline de transcrição parado')
