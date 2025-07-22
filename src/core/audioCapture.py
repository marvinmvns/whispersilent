import sounddevice as sd
import numpy as np
import queue
import threading
import time # For example usage
from config import Config
from logger import log
from audioDeviceDetector import AudioDeviceDetector

class AudioCapture:
    def __init__(self):
        self.q = queue.Queue()
        self.stream = None
        self.is_recording = False
        self.device_info = None
        self.detector = AudioDeviceDetector()

    def _callback(self, indata, frames, time, status):
        """This is called (from a separate thread) for each audio block."""
        if status:
            log.warning(f"🔴 [AUDIO CALLBACK] Status: {status}")
            print(f"🔴 [AUDIO CALLBACK] Status: {status}")
        
        # Calculate audio level for monitoring
        audio_level = np.max(np.abs(indata))
        
        # Only log significant audio activity to avoid spam
        if audio_level > 100:  # Threshold for "significant" audio
            pass  # Audio level monitoring removed
        
        # Ensure data is copied as it might be overwritten by PortAudio
        self.q.put(indata.copy())

    def _auto_detect_device(self):
        """
        Detecta automaticamente o melhor dispositivo de áudio disponível.
        Retorna o índice do dispositivo ou None se falhar.
        """
        log.info("Iniciando detecção automática de dispositivo de áudio...")
        
        try:
            # Tenta detecção automática com testes
            result = self.detector.auto_detect_best_device()
            if result:
                device_index, device_info = result
                log.info(f"✅ Dispositivo detectado automaticamente: {device_info['name']} (Índice: {device_index})")
                return device_index
            else:
                log.warning("⚠️ Detecção automática falhou, tentando dispositivo padrão")
                return None
        except Exception as e:
            log.error(f"❌ Erro na detecção automática: {e}")
            return None

    def _resolve_device(self, device_config):
        """
        Resolve o dispositivo de áudio a ser usado baseado na configuração.
        
        Args:
            device_config: Configuração do dispositivo (pode ser 'auto', índice, ou nome)
            
        Returns:
            Índice do dispositivo válido ou None se falhar
        """
        # Se configurado como 'auto', usa detecção automática
        if device_config == "auto":
            return self._auto_detect_device()
        
        # Tenta usar a configuração como índice
        try:
            device_id = int(device_config)
            # Verifica se o dispositivo existe
            device_info = sd.query_devices(device_id)
            if device_info['max_input_channels'] > 0:
                log.info(f"Usando dispositivo configurado por índice: {device_info['name']} (Índice: {device_id})")
                return device_id
            else:
                log.error(f"Dispositivo {device_id} não suporta entrada de áudio")
                return self._auto_detect_device()
        except (ValueError, sd.PortAudioError):
            # Se não é um índice válido, tenta procurar por nome
            log.info(f"Procurando dispositivo por nome: '{device_config}'")
            devices = sd.query_devices()
            
            for i, dev in enumerate(devices):
                if (device_config in dev['name'] and 
                    dev['max_input_channels'] > 0):
                    log.info(f"Dispositivo encontrado por nome: {dev['name']} (Índice: {i})")
                    return i
            
            # Se não encontrou por nome, mostra dispositivos disponíveis e tenta automático
            log.warning(f"Dispositivo '{device_config}' não encontrado")
            log.info("Dispositivos disponíveis:")
            log.info(self.detector.list_all_devices())
            return self._auto_detect_device()

    def start(self):
        if self.is_recording:
            log.info("Audio capture is already running.")
            return self.q

        try:
            device_config = Config.AUDIO["device"]
            log.debug(f"🔧 [AUDIO INIT] Configuração: {device_config}")
            device_id = self._resolve_device(device_config)
            
            if device_id is None:
                # Último recurso: usar dispositivo padrão
                log.warning("Usando dispositivo de entrada padrão do sistema")
                log.debug(f"⚠️  [AUDIO INIT] Fallback para dispositivo padrão")
                device_id = sd.default.device[0]  # Dispositivo de entrada padrão
                if device_id is None:
                    raise RuntimeError("Nenhum dispositivo de entrada disponível")

            self.device_info = sd.query_devices(device_id)
            
            # Enhanced device info logging
            log.debug(f"🎤 [AUDIO DEVICE] {self.device_info['name']} (ID: {device_id})")
            log.debug(f"    📊 Canais: {self.device_info['max_input_channels']} | Sample Rate: {self.device_info['default_samplerate']} Hz")
            log.debug(f"    ⚙️  Config: {Config.AUDIO['sample_rate']} Hz, {Config.AUDIO['channels']} canal(is)")
            
            log.debug(f"🎤 Usando dispositivo de áudio: {self.device_info['name']} (Índice: {device_id})")
            log.debug(f"   Canais de entrada: {self.device_info['max_input_channels']}")
            log.debug(f"   Taxa de amostra padrão: {self.device_info['default_samplerate']} Hz")

            self.stream = sd.InputStream(
                samplerate=Config.AUDIO["sample_rate"],
                channels=Config.AUDIO["channels"],
                device=device_id,
                callback=self._callback,
                dtype='int16' # Assuming 16-bit signed integers
            )
            self.stream.start()
            self.is_recording = True
            
            print(f"✅ [AUDIO STREAM] Captura iniciada - aguardando áudio...")
            log.info('✅ Captura de áudio iniciada com sucesso')
            return self.q # Return the queue for consumption

        except Exception as e:
            print(f"🚨 [AUDIO ERROR] Falha na inicialização: {e}")
            log.error(f'❌ Erro ao iniciar captura: {e}')
            # Mostra dispositivos disponíveis para debug
            log.info("Dispositivos de áudio disponíveis:")
            try:
                log.info(self.detector.list_all_devices())
            except:
                pass
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