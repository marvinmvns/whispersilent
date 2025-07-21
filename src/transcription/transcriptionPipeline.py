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
        try:
            # AudioCapture puts data into self.audio_queue
            # AudioProcessor consumes from self.audio_queue and yields processed chunks
            for audio_chunk in self.audio_processor.process_audio():
                if not self.is_running: # Check if pipeline is stopped
                    break
                
                if audio_chunk is not None and audio_chunk.size > 0:
                    self.health_monitor.record_chunk_processed()
                    self.processed_audio_queue.put(audio_chunk)
                    self._process_chunk_from_queue() # Process immediately or in another thread

        except Exception as e:
            log.error(f"Erro crítico no loop de processamento de áudio: {e}")
        finally:
            log.info('Loop de processamento de áudio finalizado.')
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
            
            # Transcrever áudio
            log.info(f'Processando chunk de áudio ({audio_chunk.size} samples)...')
            transcription = self.transcription_service.transcribe(audio_chunk)
            
            if transcription and transcription.strip():
                processing_time_ms = (time.time() - start_time) * 1000
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
                
                # Also store in daily file for chronological ordering
                transcription_record = {
                    "id": record_id,
                    "text": transcription,
                    "timestamp": time.time(),
                    "processing_time_ms": processing_time_ms,
                    "chunk_size": audio_chunk.size,
                    "api_sent": False
                }
                self.file_manager.append_to_daily_file(transcription_record)
                
                # Send to API only if enabled
                if self.api_sending_enabled:
                    try:
                        self.health_monitor.record_api_request_sent()
                        # Determine service type for API metadata
                        if hasattr(self.transcription_service, 'engine'):
                            service_type = f"speech-recognition-{self.transcription_service.engine.value}"
                        elif Config.GOOGLE_TRANSCRIBE["enabled"]:
                            service_type = "google-transcribe"
                        else:
                            service_type = "unknown"
                        self.api_service.send_transcription(transcription, {
                            "chunkSize": audio_chunk.size, # Size in samples
                            "processingTimeMs": processing_time_ms,
                            "recordId": record_id,
                            "transcriptionService": service_type
                        })
                        # Mark as sent in storage
                        self.transcription_storage.mark_api_sent(record_id)
                        api_sent = True
                    except Exception as api_error:
                        self.health_monitor.record_api_request_failed(str(api_error))
                        log.error(f"Failed to send transcription to API: {api_error}")
                        # Don't raise - continue processing other chunks
                else:
                    log.debug("API sending disabled - transcription stored locally only")
            else:
                log.debug('Nenhuma fala detectada no chunk')
        except Exception as e:
            log.error(f'Erro ao processar chunk: {e}')
            self.health_monitor.record_transcription_failure(str(e))
            # Continue processing next chunks even if an error occurs

    def start(self):
        if self.is_running:
            log.info("Pipeline já está em execução.")
            return

        try:
            log.info('Iniciando pipeline de transcrição...')
            
            # Start audio capture in its own thread if it blocks
            # For sounddevice, the callback runs in a separate thread, so start() itself is non-blocking
            self.audio_capture.start() # This starts the sounddevice stream and populates self.audio_queue
            self.is_running = True

            # Start the processing loop in a separate thread
            self.processing_thread = threading.Thread(target=self._processing_loop, daemon=True)
            self.processing_thread.start()

            log.info('Pipeline de transcrição iniciado com sucesso')
            log.info('Aguardando áudio... Fale no microfone!')
        except Exception as e:
            log.error(f'Erro ao iniciar pipeline: {e}')
            self.stop() # Ensure cleanup if start fails
            raise

    def stop(self):
        if self.is_running:
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
            
            log.info('Pipeline de transcrição parado')
