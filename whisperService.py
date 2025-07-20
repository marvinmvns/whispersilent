import os
import subprocess
import wave
import time
from config import Config
from logger import log

class WhisperService:
    def __init__(self):
        self.temp_file_counter = 0
        self.whisper_cpp_path = Config.WHISPER["executable_path"]
        self.initialize_whisper()

    def initialize_whisper(self):
        """Initializes Whisper by checking for the model and executable."""
        try:
            os.makedirs(Config.PROCESSING["temp_dir"], exist_ok=True)

            if not os.path.exists(Config.WHISPER["model_path"]):
                log.error(f'Whisper model not found at: {Config.WHISPER["model_path"]}')
                log.info("Run the setup script to download the model.")
                raise FileNotFoundError("Whisper model not found")
            
            if not os.path.exists(self.whisper_cpp_path):
                log.error(f"whisper.cpp executable not found at: {self.whisper_cpp_path}")
                log.info("Ensure whisper.cpp is compiled and the path is correct in config.py.")
                raise FileNotFoundError("whisper.cpp executable not found")

            log.info("Whisper initialized successfully")
        except Exception as e:
            log.error(f"Error initializing Whisper: {e}", exc_info=True)
            raise

    def save_as_wav(self, audio_data, file_path):
        """Saves a numpy array of audio data as a WAV file."""
        try:
            with wave.open(file_path, 'wb') as wf:
                wf.setnchannels(Config.AUDIO["channels"])
                wf.setsampwidth(Config.AUDIO["bit_depth"] // 8)
                wf.setframerate(Config.AUDIO["sample_rate"])
                wf.writeframes(audio_data.tobytes())
            log.debug(f"Audio saved to {file_path}")
        except Exception as e:
            log.error(f"Error saving WAV file: {e}", exc_info=True)
            raise

    def transcribe(self, audio_buffer):
        """Transcribes an audio buffer using whisper.cpp."""
        temp_file_name = f"audio_{int(time.time())}_{self.temp_file_counter}.wav"
        self.temp_file_counter += 1
        temp_file_path = os.path.join(Config.PROCESSING["temp_dir"], temp_file_name)

        try:
            self.save_as_wav(audio_buffer, temp_file_path)

            command = self._build_command(temp_file_path)
            log.debug(f"Executing whisper.cpp command: {' '.join(command)}")
            
            start_time = time.time()
            result = subprocess.run(command, capture_output=True, text=True, check=True, encoding='utf-8')
            execution_time = time.time() - start_time
            
            transcription = result.stdout.strip()

            if transcription:
                log.info(f'Transcription completed in {execution_time:.2f}s: "{transcription}"')
                return transcription
            
            log.debug("Transcription result was empty.")
            return None
        except subprocess.CalledProcessError as e:
            log.error(f"whisper.cpp execution failed: {e.stderr}")
            raise
        except Exception as e:
            log.error(f"Error during Whisper transcription: {e}", exc_info=True)
            raise
        finally:
            self._cleanup_temp_file(temp_file_path)

    def _build_command(self, file_path):
        """Builds the whisper.cpp command with configured options."""
        command = [
            self.whisper_cpp_path,
            "-m", Config.WHISPER["model_path"],
            "-l", Config.WHISPER["language"],
            "-f", file_path,
            "-t", str(Config.WHISPER["threads"]),
            "-p", str(Config.WHISPER["processors"]),
            "--no-timestamps", # Assuming no timestamps are needed by default
        ]

        if Config.WHISPER.get("enable_gpu", False):
            command.append("-ng")
        
        # Add other specific boolean flags
        if Config.WHISPER.get("no_fallback", False):
            command.append("--no-fallback")
        if Config.WHISPER.get("split_on_word", False):
            command.append("--split-on-word")

        # Add flags with values
        if Config.WHISPER.get("max_len", 0) > 0:
            command.extend(["--max-len", str(Config.WHISPER["max_len"])])

        return command

    def _cleanup_temp_file(self, file_path):
        """Removes the temporary audio file."""
        try:
            if os.path.exists(file_path):
                os.unlink(file_path)
        except Exception as e:
            log.warning(f"Error removing temporary file {file_path}: {e}")

    def cleanup(self):
        """Cleans up all temporary audio files in the temp directory."""
        try:
            temp_dir = Config.PROCESSING["temp_dir"]
            for file_name in os.listdir(temp_dir):
                if file_name.startswith('audio_') and file_name.endswith('.wav'):
                    file_path = os.path.join(temp_dir, file_name)
                    self._cleanup_temp_file(file_path)
            log.info("Temporary files cleaned up.")
        except Exception as e:
            log.warning(f"Error during cleanup of temporary files: {e}")