import speech_recognition as sr
import numpy as np
import tempfile
import os
import time
import wave
import io
from typing import Optional, Dict, Any, Union
from enum import Enum

import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'core'))
from config import Config
from logger import log

class TranscriptionEngine(Enum):
    """Available transcription engines with feature toggle support"""
    GOOGLE = "google"                    # Free Google Speech Recognition (online)
    GOOGLE_CLOUD = "google_cloud"       # Google Cloud Speech API (online, paid)
    SPHINX = "sphinx"                   # CMU Sphinx (offline)
    WIT = "wit"                         # Wit.ai (online)
    AZURE = "azure"                     # Microsoft Azure Speech (online)
    HOUNDIFY = "houndify"               # Houndify API (online)
    IBM = "ibm"                         # IBM Speech to Text (online)
    WHISPER_LOCAL = "whisper_local"     # OpenAI Whisper (offline)
    WHISPER_API = "whisper_api"         # OpenAI Whisper API (online)
    FASTER_WHISPER = "faster_whisper"   # Faster Whisper (offline)
    GROQ = "groq"                       # Groq Whisper API (online)
    VOSK = "vosk"                       # Vosk API (offline)
    CUSTOM_ENDPOINT = "custom_endpoint"  # Custom MP3 API endpoint

class SpeechRecognitionService:
    """
    Comprehensive speech recognition service supporting multiple backends
    with feature toggle configuration
    """
    
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.microphone = None
        
        # Load engine preference from config
        engine_name = Config.SPEECH_RECOGNITION.get("engine", "google").lower()
        try:
            self.engine = TranscriptionEngine(engine_name)
        except ValueError:
            log.warning(f"Invalid engine '{engine_name}', falling back to Google")
            self.engine = TranscriptionEngine.GOOGLE
            
        self.language = Config.SPEECH_RECOGNITION.get("language", "pt-BR")
        self.timeout = Config.SPEECH_RECOGNITION.get("timeout", 30)
        self.phrase_timeout = Config.SPEECH_RECOGNITION.get("phrase_timeout", 5)
        
        # Engine-specific configurations
        self._load_engine_config()
        
        log.info(f"Initialized SpeechRecognitionService with engine: {self.engine.value}")
    
    def _load_engine_config(self):
        """Load engine-specific configuration"""
        self.engine_config = {}
        
        if self.engine == TranscriptionEngine.GOOGLE_CLOUD:
            self.engine_config = {
                "credentials_json": Config.SPEECH_RECOGNITION.get("google_cloud_credentials"),
                "project_id": Config.SPEECH_RECOGNITION.get("google_cloud_project_id")
            }
        elif self.engine == TranscriptionEngine.WIT:
            self.engine_config = {
                "key": Config.SPEECH_RECOGNITION.get("wit_key")
            }
        elif self.engine == TranscriptionEngine.AZURE:
            self.engine_config = {
                "key": Config.SPEECH_RECOGNITION.get("azure_key"),
                "location": Config.SPEECH_RECOGNITION.get("azure_location", "westus")
            }
        elif self.engine == TranscriptionEngine.HOUNDIFY:
            self.engine_config = {
                "client_id": Config.SPEECH_RECOGNITION.get("houndify_client_id"),
                "client_key": Config.SPEECH_RECOGNITION.get("houndify_client_key")
            }
        elif self.engine == TranscriptionEngine.IBM:
            self.engine_config = {
                "username": Config.SPEECH_RECOGNITION.get("ibm_username"),
                "password": Config.SPEECH_RECOGNITION.get("ibm_password"),
                "url": Config.SPEECH_RECOGNITION.get("ibm_url")
            }
        elif self.engine == TranscriptionEngine.WHISPER_API:
            self.engine_config = {
                "api_key": Config.SPEECH_RECOGNITION.get("openai_api_key")
            }
        elif self.engine == TranscriptionEngine.GROQ:
            self.engine_config = {
                "api_key": Config.SPEECH_RECOGNITION.get("groq_api_key")
            }
        elif self.engine == TranscriptionEngine.WHISPER_LOCAL:
            self.engine_config = {
                "model": Config.SPEECH_RECOGNITION.get("whisper_model", "base"),
                "device": Config.SPEECH_RECOGNITION.get("whisper_device", "cpu")
            }
        elif self.engine == TranscriptionEngine.FASTER_WHISPER:
            self.engine_config = {
                "model_size": Config.SPEECH_RECOGNITION.get("faster_whisper_model", "base"),
                "device": Config.SPEECH_RECOGNITION.get("faster_whisper_device", "cpu")
            }
        elif self.engine == TranscriptionEngine.VOSK:
            self.engine_config = {
                "model_path": Config.SPEECH_RECOGNITION.get("vosk_model_path")
            }
        elif self.engine == TranscriptionEngine.CUSTOM_ENDPOINT:
            self.engine_config = {
                "endpoint": Config.SPEECH_RECOGNITION.get("custom_endpoint"),
                "api_key": Config.SPEECH_RECOGNITION.get("custom_api_key"),
                "method": Config.SPEECH_RECOGNITION.get("custom_method", "POST")
            }

    def _numpy_to_audio_data(self, audio_chunk: np.ndarray) -> sr.AudioData:
        """Convert numpy array to speech_recognition AudioData format"""
        try:
            # Ensure audio is int16
            if audio_chunk.dtype != np.int16:
                audio_chunk = (audio_chunk * 32767).astype(np.int16)
            
            # Create WAV bytes in memory
            byte_io = io.BytesIO()
            with wave.open(byte_io, 'wb') as wav_file:
                wav_file.setnchannels(Config.AUDIO["channels"])
                wav_file.setsampwidth(2)  # 16-bit
                wav_file.setframerate(Config.AUDIO["sample_rate"])
                wav_file.writeframes(audio_chunk.tobytes())
            
            # Create AudioData object
            byte_io.seek(0)
            audio_data = sr.AudioData(
                byte_io.getvalue(), 
                Config.AUDIO["sample_rate"], 
                2  # 16-bit = 2 bytes
            )
            
            return audio_data
            
        except Exception as e:
            log.error(f"Error converting numpy array to AudioData: {e}")
            raise

    def _recognize_with_engine(self, audio_data: sr.AudioData) -> str:
        """Perform recognition using the configured engine"""
        try:
            if self.engine == TranscriptionEngine.GOOGLE:
                return self.recognizer.recognize_google(
                    audio_data, 
                    language=self.language
                )
            
            elif self.engine == TranscriptionEngine.GOOGLE_CLOUD:
                credentials_json = self.engine_config.get("credentials_json")
                if credentials_json:
                    return self.recognizer.recognize_google_cloud(
                        audio_data,
                        credentials_json=credentials_json,
                        language=self.language,
                        preferred_phrases=None
                    )
                else:
                    raise ValueError("Google Cloud credentials not configured")
            
            elif self.engine == TranscriptionEngine.SPHINX:
                return self.recognizer.recognize_sphinx(
                    audio_data,
                    language=self.language.split('-')[0]  # Sphinx uses 'pt' not 'pt-BR'
                )
            
            elif self.engine == TranscriptionEngine.WIT:
                key = self.engine_config.get("key")
                if key:
                    return self.recognizer.recognize_wit(audio_data, key=key)
                else:
                    raise ValueError("Wit.ai key not configured")
            
            elif self.engine == TranscriptionEngine.AZURE:
                key = self.engine_config.get("key")
                location = self.engine_config.get("location")
                if key:
                    return self.recognizer.recognize_azure(
                        audio_data,
                        key=key,
                        location=location,
                        language=self.language
                    )
                else:
                    raise ValueError("Azure Speech key not configured")
            
            elif self.engine == TranscriptionEngine.HOUNDIFY:
                client_id = self.engine_config.get("client_id")
                client_key = self.engine_config.get("client_key")
                if client_id and client_key:
                    return self.recognizer.recognize_houndify(
                        audio_data,
                        client_id=client_id,
                        client_key=client_key
                    )
                else:
                    raise ValueError("Houndify credentials not configured")
            
            elif self.engine == TranscriptionEngine.IBM:
                username = self.engine_config.get("username")
                password = self.engine_config.get("password")
                url = self.engine_config.get("url")
                if username and password:
                    return self.recognizer.recognize_ibm(
                        audio_data,
                        username=username,
                        password=password,
                        language=self.language,
                        url=url
                    )
                else:
                    raise ValueError("IBM Speech credentials not configured")
            
            elif self.engine == TranscriptionEngine.WHISPER_LOCAL:
                model = self.engine_config.get("model", "base")
                return self.recognizer.recognize_whisper(
                    audio_data,
                    model=model,
                    language=self.language.split('-')[0]  # Whisper uses 'pt' not 'pt-BR'
                )
            
            elif self.engine == TranscriptionEngine.WHISPER_API:
                api_key = self.engine_config.get("api_key")
                if api_key:
                    return self.recognizer.recognize_openai(
                        audio_data,
                        api_key=api_key,
                        language=self.language.split('-')[0]
                    )
                else:
                    raise ValueError("OpenAI API key not configured")
            
            elif self.engine == TranscriptionEngine.FASTER_WHISPER:
                model_size = self.engine_config.get("model_size", "base")
                device = self.engine_config.get("device", "cpu")
                return self.recognizer.recognize_faster_whisper(
                    audio_data,
                    model_size=model_size,
                    device=device,
                    language=self.language.split('-')[0]
                )
            
            elif self.engine == TranscriptionEngine.GROQ:
                api_key = self.engine_config.get("api_key")
                if api_key:
                    return self.recognizer.recognize_groq(
                        audio_data,
                        api_key=api_key,
                        language=self.language.split('-')[0]
                    )
                else:
                    raise ValueError("Groq API key not configured")
            
            elif self.engine == TranscriptionEngine.VOSK:
                model_path = self.engine_config.get("model_path")
                if model_path and os.path.exists(model_path):
                    return self._recognize_vosk_custom(audio_data, model_path)
                else:
                    raise ValueError("Vosk model path not configured or not found")
            
            elif self.engine == TranscriptionEngine.CUSTOM_ENDPOINT:
                # Use the existing GoogleTranscribeService for custom endpoints
                from googleTranscribeService import GoogleTranscribeService
                custom_service = GoogleTranscribeService()
                # Convert AudioData back to numpy array for custom service
                wav_data = audio_data.get_wav_data()
                # This is a simplified conversion - you might need to adjust
                return custom_service._send_audio_to_api_direct(wav_data)
            
            else:
                raise ValueError(f"Unsupported engine: {self.engine}")
                
        except sr.UnknownValueError:
            log.debug(f"No speech detected by {self.engine.value}")
            return ""
        except sr.RequestError as e:
            log.error(f"API request failed for {self.engine.value}: {e}")
            raise
        except Exception as e:
            log.error(f"Recognition error with {self.engine.value}: {e}")
            raise

    def transcribe(self, audio_chunk: np.ndarray) -> str:
        """
        Main transcription method - converts numpy audio array to text
        
        Args:
            audio_chunk: numpy array of audio samples (int16 or float)
            
        Returns:
            str: Transcribed text or empty string if no speech detected
        """
        try:
            start_time = time.time()
            
            # Debug output to log
            log.debug(f'Processing audio chunk ({audio_chunk.size} samples) with {self.engine.value}...')
            
            # Convert numpy array to AudioData
            audio_data = self._numpy_to_audio_data(audio_chunk)
            
            # Perform recognition
            transcription = self._recognize_with_engine(audio_data)
            
            processing_time_ms = (time.time() - start_time) * 1000
            
            if transcription and transcription.strip():
                # Prominent console output for successful transcription
                print(f"✅ [TRANSCRIÇÃO] ({processing_time_ms:.2f}ms): \"{transcription}\"")
                log.info(f'{self.engine.value} transcription in {processing_time_ms:.2f}ms: "{transcription}"')
                return transcription.strip()
            else:
                log.debug(f"No speech detected ({self.engine.value})")
                log.debug(f'No speech detected by {self.engine.value}')
                return ""
                
        except Exception as e:
            print(f"🚨 [ERRO] Falha na transcrição ({self.engine.value}): {e}")
            log.error(f'Transcription failed with {self.engine.value}: {e}')
            # Don't raise - return empty string to continue processing
            return ""

    def get_engine_info(self) -> Dict[str, Any]:
        """Get information about the current engine"""
        engine_info = {
            "engine": self.engine.value,
            "language": self.language,
            "offline": self.is_offline_engine(),
            "requires_api_key": self.requires_api_key(),
            "status": "ready"
        }
        
        # Add engine-specific status information
        if self.engine == TranscriptionEngine.VOSK:
            model_path = self.engine_config.get("model_path")
            engine_info["model_available"] = bool(model_path and os.path.exists(model_path))
        
        return engine_info

    def is_offline_engine(self) -> bool:
        """Check if the current engine works offline"""
        offline_engines = {
            TranscriptionEngine.SPHINX,
            TranscriptionEngine.WHISPER_LOCAL,
            TranscriptionEngine.FASTER_WHISPER,
            TranscriptionEngine.VOSK
        }
        return self.engine in offline_engines

    def requires_api_key(self) -> bool:
        """Check if the current engine requires an API key"""
        api_key_engines = {
            TranscriptionEngine.GOOGLE_CLOUD,
            TranscriptionEngine.WIT,
            TranscriptionEngine.AZURE,
            TranscriptionEngine.HOUNDIFY,
            TranscriptionEngine.IBM,
            TranscriptionEngine.WHISPER_API,
            TranscriptionEngine.GROQ,
            TranscriptionEngine.CUSTOM_ENDPOINT
        }
        return self.engine in api_key_engines

    def cleanup(self):
        """Cleanup method for compatibility with other transcription services"""
        log.debug(f"SpeechRecognitionService ({self.engine.value}) cleanup completed")
        pass

    def switch_engine(self, engine_name: str) -> bool:
        """
        Switch to a different recognition engine
        
        Args:
            engine_name: Name of the engine to switch to
            
        Returns:
            bool: True if switch was successful
        """
        try:
            new_engine = TranscriptionEngine(engine_name.lower())
            old_engine = self.engine
            self.engine = new_engine
            self._load_engine_config()
            log.info(f"Switched from {old_engine.value} to {new_engine.value}")
            return True
        except ValueError:
            log.error(f"Invalid engine name: {engine_name}")
            return False

    def _recognize_vosk_custom(self, audio_data, model_path: str) -> str:
        """
        Custom Vosk recognition that uses the specified model path instead of hardcoded 'model' folder
        
        Args:
            audio_data: AudioData object from speech_recognition
            model_path: Path to the Vosk model directory
            
        Returns:
            str: Transcribed text
        """
        try:
            from vosk import KaldiRecognizer, Model
            import json
            
            # Initialize model if not already done
            if not hasattr(self, 'vosk_model') or self._current_vosk_model_path != model_path:
                log.info(f"Loading Vosk model from: {model_path}")
                self.vosk_model = Model(model_path)
                self._current_vosk_model_path = model_path
            
            # Create recognizer with 16kHz sample rate
            rec = KaldiRecognizer(self.vosk_model, 16000)
            
            # Convert audio data to the format Vosk expects
            raw_data = audio_data.get_raw_data(convert_rate=16000, convert_width=2)
            
            # Process the audio
            rec.AcceptWaveform(raw_data)
            result = rec.FinalResult()
            
            # Parse the JSON result
            result_dict = json.loads(result)
            return result_dict.get('text', '')
            
        except ImportError:
            raise ValueError("Vosk library not installed. Install with: pip install vosk")
        except Exception as e:
            raise ValueError(f"Vosk recognition failed: {e}")

if __name__ == '__main__':
    # Test the service with different engines
    import numpy as np
    
    # Create sample audio data for testing
    sample_rate = 16000
    duration = 3  # 3 seconds
    t = np.linspace(0, duration, sample_rate * duration)
    audio_data = (np.sin(2 * np.pi * 440 * t) * 32767 * 0.1).astype(np.int16)  # 440 Hz tone
    
    # Test with Google (free) engine
    try:
        service = SpeechRecognitionService()
        print(f"Testing {service.engine.value} engine...")
        print(f"Engine info: {service.get_engine_info()}")
        
        # This will likely return empty since it's just a tone, but tests the pipeline
        result = service.transcribe(audio_data)
        print(f"Transcription result: '{result}'")
        
    except Exception as e:
        log.error(f"Test failed: {e}")