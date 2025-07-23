import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    AUDIO = {
        "sample_rate": int(os.getenv("SAMPLE_RATE", 16000)),
        "channels": int(os.getenv("CHANNELS", 1)),
        "device": os.getenv("AUDIO_DEVICE", "auto"),  # 'auto' para detecção automática, ou índice/nome específico
        "file_type": "wav",
        "encoding": "signed-integer",
        "bit_depth": 16
    }

    WHISPER = {
        "model_path": os.getenv("WHISPER_MODEL_PATH", os.path.join(os.path.dirname(__file__), "models", "ggml-base.bin")),
        "language": os.getenv("WHISPER_LANGUAGE", "pt"),
        "enable_gpu": os.getenv("ENABLE_GPU", "false").lower() == "true",
        "threads": 4,  # Otimizado para Raspberry Pi 2W
        "processors": 1,
        "max_len": 0,
        "split_on_word": True,
        "no_fallback": False,
        "print_progress": False,
        "print_realtime": False,
        "print_timestamps": False,
        "executable_path": os.getenv("WHISPER_EXECUTABLE_PATH", os.path.join(os.path.dirname(__file__), "whisper.cpp", "build", "bin", "main"))
    }

    API = {
        "endpoint": os.getenv("API_ENDPOINT"),
        "key": os.getenv("API_KEY"),
        "timeout": 30000,
        "retry_attempts": 3,
        "retry_delay": 1000
    }

    GOOGLE_TRANSCRIBE = {
        "enabled": os.getenv("GOOGLE_TRANSCRIBE_ENABLED", "false").lower() == "true",
        "endpoint": os.getenv("GOOGLE_TRANSCRIBE_ENDPOINT"),
        "key": os.getenv("GOOGLE_TRANSCRIBE_KEY"),
        "language": os.getenv("GOOGLE_TRANSCRIBE_LANGUAGE", "pt-BR"),
        "timeout": 30000,
        "retry_attempts": 3,
        "retry_delay": 1000
    }

    SPEECH_RECOGNITION = {
        # Engine selection: google, google_cloud, sphinx, wit, azure, houndify, ibm, 
        # whisper_local, whisper_api, faster_whisper, groq, vosk, custom_endpoint
        "engine": os.getenv("SPEECH_RECOGNITION_ENGINE", "google"),
        "language": os.getenv("SPEECH_RECOGNITION_LANGUAGE", "pt-BR"),
        "timeout": int(os.getenv("SPEECH_RECOGNITION_TIMEOUT", "30")),
        "phrase_timeout": int(os.getenv("SPEECH_RECOGNITION_PHRASE_TIMEOUT", "5")),
        
        # Fallback configuration
        "enable_fallback": os.getenv("SPEECH_RECOGNITION_ENABLE_FALLBACK", "true").lower() == "true",
        "offline_fallback_engine": os.getenv("SPEECH_RECOGNITION_OFFLINE_FALLBACK", "vosk"),
        "auto_switch_on_connection_loss": os.getenv("SPEECH_RECOGNITION_AUTO_SWITCH", "true").lower() == "true",
        "connectivity_check_interval": int(os.getenv("CONNECTIVITY_CHECK_INTERVAL", "30")),
        
        # Google Cloud Speech API
        "google_cloud_credentials": os.getenv("GOOGLE_CLOUD_CREDENTIALS_JSON"),
        "google_cloud_project_id": os.getenv("GOOGLE_CLOUD_PROJECT_ID"),
        
        # Wit.ai
        "wit_key": os.getenv("WIT_AI_KEY"),
        
        # Microsoft Azure Speech
        "azure_key": os.getenv("AZURE_SPEECH_KEY"),
        "azure_location": os.getenv("AZURE_SPEECH_LOCATION", "westus"),
        
        # Houndify
        "houndify_client_id": os.getenv("HOUNDIFY_CLIENT_ID"),
        "houndify_client_key": os.getenv("HOUNDIFY_CLIENT_KEY"),
        
        # IBM Speech to Text
        "ibm_username": os.getenv("IBM_SPEECH_USERNAME"),
        "ibm_password": os.getenv("IBM_SPEECH_PASSWORD"),
        "ibm_url": os.getenv("IBM_SPEECH_URL"),
        
        # OpenAI Whisper API
        "openai_api_key": os.getenv("OPENAI_API_KEY"),
        
        # Groq Whisper API
        "groq_api_key": os.getenv("GROQ_API_KEY"),
        
        # Local Whisper
        "whisper_model": os.getenv("WHISPER_MODEL", "base"),
        "whisper_device": os.getenv("WHISPER_DEVICE", "cpu"),
        
        # Faster Whisper
        "faster_whisper_model": os.getenv("FASTER_WHISPER_MODEL", "base"),
        "faster_whisper_device": os.getenv("FASTER_WHISPER_DEVICE", "cpu"),
        
        # Vosk
        "vosk_model_path": os.getenv("VOSK_MODEL_PATH"),
        
        # Custom Endpoint
        "custom_endpoint": os.getenv("CUSTOM_SPEECH_ENDPOINT"),
        "custom_api_key": os.getenv("CUSTOM_SPEECH_API_KEY"),
        "custom_method": os.getenv("CUSTOM_SPEECH_METHOD", "POST")
    }

    PROCESSING = {
        "chunk_duration_ms": int(os.getenv("CHUNK_DURATION_MS", 3000)),
        "silence_threshold": int(os.getenv("SILENCE_THRESHOLD", 500)),
        "silence_duration_ms": int(os.getenv("SILENCE_DURATION_MS", 1500)),
        "buffer_size": 4096,
        "temp_dir": os.path.join(os.path.dirname(__file__), "temp")
    }

    HTTP_SERVER = {
        "host": os.getenv("HTTP_HOST", "localhost"),
        "port": int(os.getenv("HTTP_PORT", 8080))
    }

    LOGGING = {
        "level": os.getenv("LOG_LEVEL", "INFO").upper(),
        "log_file": os.getenv("LOG_FILE", "logs/whisper_silent.log")
    }

    SPEAKER_IDENTIFICATION = {
        "enabled": os.getenv("SPEAKER_IDENTIFICATION_ENABLED", "false").lower() == "true",
        "method": os.getenv("SPEAKER_IDENTIFICATION_METHOD", "disabled"),  # disabled, simple_energy, pyannote, resemblyzer, speechbrain
        "confidence_threshold": float(os.getenv("SPEAKER_CONFIDENCE_THRESHOLD", "0.7")),
        "min_segment_duration": float(os.getenv("SPEAKER_MIN_SEGMENT_DURATION", "2.0")),
        "max_speakers": int(os.getenv("SPEAKER_MAX_SPEAKERS", "10")),
        "energy_threshold": float(os.getenv("SPEAKER_ENERGY_THRESHOLD", "0.01")),
        "smoothing_window": int(os.getenv("SPEAKER_SMOOTHING_WINDOW", "5")),
        
        # PyAnnote configuration
        "pyannote_model_path": os.getenv("PYANNOTE_MODEL_PATH"),
        "hf_token": os.getenv("HUGGINGFACE_TOKEN"),
        
        # SpeechBrain configuration
        "speechbrain_model": os.getenv("SPEECHBRAIN_MODEL", "speechbrain/spkrec-ecapa-voxceleb")
    }

    REALTIME_API = {
        "enabled": os.getenv("REALTIME_API_ENABLED", "false").lower() == "true",
        "websocket_port": int(os.getenv("REALTIME_WEBSOCKET_PORT", 8081)),
        "max_connections": int(os.getenv("REALTIME_MAX_CONNECTIONS", 50)),
        "buffer_size": int(os.getenv("REALTIME_BUFFER_SIZE", 100)),
        "heartbeat_interval": int(os.getenv("REALTIME_HEARTBEAT_INTERVAL", 30))
    }
