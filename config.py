import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    AUDIO = {
        "sample_rate": int(os.getenv("SAMPLE_RATE", 16000)),
        "channels": int(os.getenv("CHANNELS", 1)),
        "device": "plughw:2,0",  # Seeed VoiceCard device
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

    PROCESSING = {
        "chunk_duration_ms": int(os.getenv("CHUNK_DURATION_MS", 3000)),
        "silence_threshold": int(os.getenv("SILENCE_THRESHOLD", 500)),
        "silence_duration_ms": int(os.getenv("SILENCE_DURATION_MS", 1500)),
        "buffer_size": 4096,
        "temp_dir": os.path.join(os.path.dirname(__file__), "temp")
    }
