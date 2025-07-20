import sounddevice as sd
import numpy as np
import queue
import threading
import time # For example usage
from config import Config
from logger import log

class AudioCapture:
    def __init__(self):
        self.q = queue.Queue()
        self.stream = None
        self.is_recording = False
        self.device_info = None

    def _callback(self, indata, frames, time, status):
        """This is called (from a separate thread) for each audio block."""
        if status:
            log.warning(f"Audio callback status: {status}")
        # Ensure data is copied as it might be overwritten by PortAudio
        self.q.put(indata.copy())

    def start(self):
        if self.is_recording:
            log.info("Audio capture is already running.")
            return self.q

        try:
            device_name_or_index = Config.AUDIO["device"]
            device_id = None

            try:
                # Try to interpret as an integer index first
                device_id = int(device_name_or_index)
                # Verify if the device exists
                sd.query_devices(device_id)
            except ValueError:
                # If not an integer, try to find by name
                devices = sd.query_devices()
                found_device = False
                for i, dev in enumerate(devices):
                    if device_name_or_index in dev['name']:
                        device_id = i
                        found_device = True
                        break
                if not found_device:
                    log.error(f"Audio device '{device_name_or_index}' not found. Available devices: {sd.query_devices()}")
                    raise ValueError(f"Audio device '{device_name_or_index}' not found.")
            except sd.PortAudioError:
                log.error(f"Audio device with index {device_name_or_index} does not exist.")
                raise

            self.device_info = sd.query_devices(device_id)
            log.info(f"Using audio device: {self.device_info['name']} (Index: {device_id})")

            self.stream = sd.InputStream(
                samplerate=Config.AUDIO["sample_rate"],
                channels=Config.AUDIO["channels"],
                device=device_id,
                callback=self._callback,
                dtype='int16' # Assuming 16-bit signed integers
            )
            self.stream.start()
            self.is_recording = True
            log.info('Captura de áudio iniciada')
            return self.q # Return the queue for consumption

        except Exception as e:
            log.error(f'Erro ao iniciar captura: {e}')
            self.stop() # Ensure stream is stopped if start fails
            raise

    def stop(self):
        if self.stream and self.is_recording:
            self.stream.stop()
            self.stream.close()
            self.is_recording = False
            log.info('Captura de áudio parada')
            # Clear the queue on stop to prevent old data from being processed
            with self.q.mutex:
                self.q.queue.clear()

    def get_audio_chunk(self):
        """Generator to yield audio chunks from the queue."""
        while self.is_recording or not self.q.empty():
            try:
                yield self.q.get(timeout=0.1) # Get with a timeout to allow graceful exit
            except queue.Empty:
                if not self.is_recording: # If not recording and queue is empty, exit
                    break
                # If still recording, continue waiting for data
                continue