import requests
import time
import os
import tempfile
import subprocess
from config import Config
from logger import log
import numpy as np
import wave

class GoogleTranscribeService:
    def __init__(self):
        self.endpoint = Config.GOOGLE_TRANSCRIBE["endpoint"]
        self.api_key = Config.GOOGLE_TRANSCRIBE["key"]
        self.language = Config.GOOGLE_TRANSCRIBE["language"]
        self.timeout = Config.GOOGLE_TRANSCRIBE["timeout"] / 1000  # Convert ms to seconds
        self.retry_attempts = Config.GOOGLE_TRANSCRIBE["retry_attempts"]
        self.retry_delay = Config.GOOGLE_TRANSCRIBE["retry_delay"]
        
        # Headers for API requests
        self.headers = {}
        if self.api_key:
            self.headers['Authorization'] = f'Bearer {self.api_key}'

    def _log_request(self, method, url):
        log.debug(f'Google Transcribe Request: {{ "method": "{method}", "url": "{url}", "language": "{self.language}" }}')

    def _log_response(self, status, data):
        log.debug(f'Google Transcribe Response: {{ "status": {status}, "data": {data} }}')

    def _log_error(self, message, error_details=None):
        log.error(f'Google Transcribe Error: {message}', extra={'error_details': error_details})

    def _audio_to_wav(self, audio_chunk):
        """Convert numpy audio array to WAV file"""
        try:
            # Create temporary WAV file
            temp_wav = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
            temp_wav.close()
            
            # Write audio data to WAV file
            with wave.open(temp_wav.name, 'wb') as wav_file:
                wav_file.setnchannels(Config.AUDIO["channels"])
                wav_file.setsampwidth(2)  # 16-bit
                wav_file.setframerate(Config.AUDIO["sample_rate"])
                
                # Convert numpy array to bytes
                if audio_chunk.dtype != np.int16:
                    # Convert float to int16 if necessary
                    audio_chunk = (audio_chunk * 32767).astype(np.int16)
                
                wav_file.writeframes(audio_chunk.tobytes())
            
            return temp_wav.name
        except Exception as e:
            log.error(f"Error creating WAV file: {e}")
            raise

    def _wav_to_mp3(self, wav_path):
        """Convert WAV file to MP3 using ffmpeg"""
        try:
            # Create temporary MP3 file
            temp_mp3 = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3')
            temp_mp3.close()
            
            # Use ffmpeg to convert WAV to MP3
            cmd = [
                'ffmpeg', '-y',  # -y to overwrite output file
                '-i', wav_path,
                '-acodec', 'mp3',
                '-ab', '128k',  # 128 kbps bitrate
                '-ar', str(Config.AUDIO["sample_rate"]),
                '-ac', str(Config.AUDIO["channels"]),
                temp_mp3.name
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode != 0:
                raise Exception(f"ffmpeg failed: {result.stderr}")
            
            return temp_mp3.name
        except subprocess.TimeoutExpired:
            log.error("ffmpeg conversion timed out")
            raise Exception("Audio conversion timed out")
        except FileNotFoundError:
            log.error("ffmpeg not found. Please install ffmpeg to use Google Transcribe service")
            raise Exception("ffmpeg not found")
        except Exception as e:
            log.error(f"Error converting to MP3: {e}")
            raise

    def _cleanup_temp_files(self, *file_paths):
        """Clean up temporary files"""
        for file_path in file_paths:
            try:
                if file_path and os.path.exists(file_path):
                    os.unlink(file_path)
            except Exception as e:
                log.warning(f"Could not delete temporary file {file_path}: {e}")

    def transcribe(self, audio_chunk):
        """
        Transcribe audio chunk by converting to MP3 and sending to external API
        """
        if not self.endpoint:
            log.error("Google Transcribe endpoint not configured")
            raise ValueError("GOOGLE_TRANSCRIBE_ENDPOINT not set")

        wav_path = None
        mp3_path = None
        
        try:
            # Convert audio chunk to WAV
            log.debug(f'Converting audio chunk ({audio_chunk.size} samples) to WAV...')
            wav_path = self._audio_to_wav(audio_chunk)
            
            # Convert WAV to MP3
            log.debug('Converting WAV to MP3...')
            mp3_path = self._wav_to_mp3(wav_path)
            
            # Send MP3 to transcription API
            log.debug('Sending MP3 to transcription service...')
            transcription = self._send_audio_to_api(mp3_path)
            
            return transcription
            
        except Exception as e:
            log.error(f"Error in transcription process: {e}")
            raise
        finally:
            # Clean up temporary files
            self._cleanup_temp_files(wav_path, mp3_path)

    def _send_audio_to_api(self, mp3_path):
        """Send MP3 file to external transcription API"""
        for attempt in range(self.retry_attempts):
            try:
                url = self.endpoint
                self._log_request('POST', url)
                
                # Prepare multipart form data
                files = {
                    'audio': ('audio.mp3', open(mp3_path, 'rb'), 'audio/mpeg')
                }
                
                data = {
                    'language': self.language,
                    'sample_rate': Config.AUDIO["sample_rate"],
                    'channels': Config.AUDIO["channels"],
                    'device': 'raspberry-pi-2w'
                }
                
                response = requests.post(
                    url, 
                    files=files, 
                    data=data, 
                    headers=self.headers, 
                    timeout=self.timeout
                )
                
                # Close the file
                files['audio'][1].close()
                
                response.raise_for_status()
                
                result = response.json()
                self._log_response(response.status_code, result)
                
                # Extract transcription text from response
                # Adjust this based on your API response format
                transcription = result.get('transcription', '') or result.get('text', '')
                
                if transcription:
                    log.info(f'Google Transcribe successful: "{transcription}"')
                    return transcription.strip()
                else:
                    log.warning('No transcription text found in API response')
                    return ""
                    
            except requests.exceptions.RequestException as e:
                is_last_attempt = (attempt == self.retry_attempts - 1)
                error_message = str(e)
                if hasattr(e, 'response') and e.response is not None:
                    error_message = f"{e.response.status_code} - {e.response.text}"
                
                self._log_error(f"Erro ao enviar áudio para transcrição (tentativa {attempt + 1}/{self.retry_attempts}): {error_message}")
                
                if not is_last_attempt:
                    delay = self.retry_delay * (attempt + 1) / 1000  # Convert ms to seconds
                    log.info(f"Aguardando {delay}s antes da próxima tentativa...")
                    time.sleep(delay)
                else:
                    raise  # Re-raise the last exception

    def cleanup(self):
        """Cleanup method for compatibility with WhisperService interface"""
        log.debug("Google Transcribe Service cleanup completed")
        pass

if __name__ == '__main__':
    # Test example
    import numpy as np
    
    # Create sample audio data for testing
    sample_rate = 16000
    duration = 3  # 3 seconds
    t = np.linspace(0, duration, sample_rate * duration)
    audio_data = (np.sin(2 * np.pi * 440 * t) * 32767 * 0.1).astype(np.int16)  # 440 Hz tone
    
    try:
        service = GoogleTranscribeService()
        result = service.transcribe(audio_data)
        print(f"Transcription result: {result}")
    except Exception as e:
        log.error(f"Test failed: {e}")