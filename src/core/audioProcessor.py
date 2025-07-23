import numpy as np
import time
import queue
from config import Config
from logger import log

class AudioProcessor:
    def __init__(self, audio_queue):
        self.audio_queue = audio_queue
        self.buffer = np.array([], dtype=np.int16) # Buffer to accumulate samples
        self.silence_start_time = None
        self.speaking = False
        self.current_audio_chunk = np.array([], dtype=np.int16)

        # Calculate chunk size in samples based on duration and sample rate
        self.max_chunk_samples = int(Config.AUDIO["sample_rate"] * (Config.PROCESSING["chunk_duration_ms"] / 1000))
        
        # Convert bufferSize from bytes (as in JS config) to samples
        # Assuming 16-bit audio (2 bytes per sample)
        self.buffer_process_samples = Config.PROCESSING["buffer_size"] // (Config.AUDIO["bit_depth"] // 8)

        log.debug(f"AudioProcessor initialized: max_chunk_samples={self.max_chunk_samples}, buffer_process_samples={self.buffer_process_samples}")

    def detect_silence(self, audio_frame):
        """Detects silence in a given audio frame (numpy array of int16 samples)."""
        if audio_frame.size == 0:
            return True
        # Calculate the average absolute amplitude
        average_amplitude = np.mean(np.abs(audio_frame))
        return average_amplitude < Config.PROCESSING["silence_threshold"]

    def process_audio(self):
        """Generator that processes audio from the queue and yields speech chunks."""
        while True:
            try:
                # Get data from the queue. Use a timeout to allow graceful shutdown.
                # The `None` check is a placeholder for a proper shutdown mechanism.
                new_data = self.audio_queue.get(timeout=0.1)
                if new_data is None: # Signal to stop processing
                    break

                # Flatten the array if it's multi-channel and we want mono processing
                # sounddevice typically returns (frames, channels) for multi-channel
                if new_data.ndim > 1:
                    # For simplicity, taking the first channel or averaging could be options.
                    # Here, assuming mono input or flattening for processing.
                    new_data = new_data.flatten() # This will interleave channels if not mono
                    # If strictly mono processing is needed, consider: new_data = new_data[:, 0] 

                self.buffer = np.concatenate((self.buffer, new_data))

                while self.buffer.size >= self.buffer_process_samples:
                    frame = self.buffer[:self.buffer_process_samples]
                    self.buffer = self.buffer[self.buffer_process_samples:]

                    is_silent = self.detect_silence(frame)

                    if not is_silent and not self.speaking:
                        # Speech starts
                        self.speaking = True
                        self.silence_start_time = None
                        self.current_audio_chunk = np.concatenate((self.current_audio_chunk, frame))
                        log.debug('Fala detectada')
                    elif is_silent and self.speaking:
                        # Possible end of speech
                        if self.silence_start_time is None:
                            self.silence_start_time = time.time()

                        self.current_audio_chunk = np.concatenate((self.current_audio_chunk, frame))

                        # Check if silence duration exceeds threshold
                        if (time.time() - self.silence_start_time) * 1000 > Config.PROCESSING["silence_duration_ms"]:
                            # End of speech confirmed
                            self.speaking = False
                            if self.current_audio_chunk.size > 0:
                                yield self.current_audio_chunk # Yield the chunk
                                log.debug(f'Fim da fala detectado, enviando chunk de {self.current_audio_chunk.size} samples')
                                self.current_audio_chunk = np.array([], dtype=np.int16)
                    elif self.speaking:
                        # Still speaking
                        self.current_audio_chunk = np.concatenate((self.current_audio_chunk, frame))

                        # If chunk reaches max size, yield it
                        if self.current_audio_chunk.size >= self.max_chunk_samples:
                            yield self.current_audio_chunk # Yield the chunk
                            log.debug(f'Chunk máximo atingido, enviando {self.current_audio_chunk.size} samples')
                            self.current_audio_chunk = np.array([], dtype=np.int16)

            except queue.Empty:
                # No data in queue, continue waiting unless a stop signal is received
                pass
            except Exception as e:
                log.error(f"Erro no processamento de áudio: {e}")
                break # Exit loop on error

        # Flush any remaining audio when processing stops
        if self.current_audio_chunk.size > 0:
            yield self.current_audio_chunk
            log.debug(f'Flush: enviando último chunk de {self.current_audio_chunk.size} samples')
