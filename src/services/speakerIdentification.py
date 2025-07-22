"""
Speaker Identification and Diarization Service
Provides speaker identification and diarization capabilities as a feature toggle
"""

import os
import time
import numpy as np
import threading
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from enum import Enum
import hashlib
from logger import log
from config import Config

class SpeakerMethod(Enum):
    """Available speaker identification methods"""
    DISABLED = "disabled"
    SIMPLE_ENERGY = "simple_energy"
    PYANNOTE = "pyannote"
    RESEMBLYZER = "resemblyzer"
    SPEECHBRAIN = "speechbrain"

@dataclass
class SpeakerSegment:
    """Represents a speaker segment within audio"""
    start_time: float
    end_time: float
    speaker_id: str
    confidence: float
    text: Optional[str] = None
    audio_features: Optional[Dict[str, float]] = None

@dataclass
class SpeakerProfile:
    """Speaker profile for identification"""
    speaker_id: str
    name: Optional[str]
    voice_features: Dict[str, Any]
    sample_count: int
    created_at: float
    last_seen: float
    confidence_threshold: float = 0.7

class SpeakerIdentificationService:
    """
    Feature-toggleable speaker identification service
    
    Supports multiple methods:
    - Simple energy-based segmentation
    - Advanced neural speaker diarization (PyAnnote, Resemblyzer, SpeechBrain)
    - Custom speaker profiles and recognition
    """
    
    def __init__(self):
        self.enabled = Config.SPEAKER_IDENTIFICATION.get("enabled", False)
        self.method = SpeakerMethod(Config.SPEAKER_IDENTIFICATION.get("method", "disabled"))
        self.min_segment_duration = Config.SPEAKER_IDENTIFICATION.get("min_segment_duration", 2.0)
        self.confidence_threshold = Config.SPEAKER_IDENTIFICATION.get("confidence_threshold", 0.7)
        self.max_speakers = Config.SPEAKER_IDENTIFICATION.get("max_speakers", 10)
        
        # Speaker profiles storage
        self.speaker_profiles: Dict[str, SpeakerProfile] = {}
        self.segment_history: List[SpeakerSegment] = []
        self.lock = threading.Lock()
        
        # Method-specific initialization
        self.model = None
        self.initialized = False
        
        if self.enabled:
            self._initialize_method()
        
        log.info(f"SpeakerIdentificationService initialized: enabled={self.enabled}, method={self.method.value}")
    
    def _initialize_method(self):
        """Initialize the selected speaker identification method"""
        try:
            if self.method == SpeakerMethod.SIMPLE_ENERGY:
                self._initialize_simple_energy()
            elif self.method == SpeakerMethod.PYANNOTE:
                self._initialize_pyannote()
            elif self.method == SpeakerMethod.RESEMBLYZER:
                self._initialize_resemblyzer()
            elif self.method == SpeakerMethod.SPEECHBRAIN:
                self._initialize_speechbrain()
            else:
                log.warning(f"Speaker identification method '{self.method.value}' not implemented")
                return
                
            self.initialized = True
            log.info(f"Speaker identification method '{self.method.value}' initialized successfully")
            
        except ImportError as e:
            log.error(f"Failed to import required libraries for {self.method.value}: {e}")
            log.info("Speaker identification disabled due to missing dependencies")
            self.enabled = False
        except Exception as e:
            log.error(f"Failed to initialize speaker identification method {self.method.value}: {e}")
            self.enabled = False
    
    def _initialize_simple_energy(self):
        """Initialize simple energy-based speaker segmentation"""
        # No external dependencies needed for simple method
        self.energy_threshold = Config.SPEAKER_IDENTIFICATION.get("energy_threshold", 0.01)
        self.smoothing_window = Config.SPEAKER_IDENTIFICATION.get("smoothing_window", 5)
        log.debug("Simple energy-based speaker segmentation initialized")
    
    def _initialize_pyannote(self):
        """Initialize PyAnnote.audio for speaker diarization"""
        try:
            from pyannote.audio import Pipeline
            
            model_path = Config.SPEAKER_IDENTIFICATION.get("pyannote_model_path")
            if model_path and os.path.exists(model_path):
                self.model = Pipeline.from_pretrained(model_path)
            else:
                # Use default pretrained model (requires HuggingFace token)
                self.model = Pipeline.from_pretrained("pyannote/speaker-diarization-3.1",
                                                    use_auth_token=Config.SPEAKER_IDENTIFICATION.get("hf_token"))
            
            log.debug("PyAnnote speaker diarization model loaded")
            
        except ImportError:
            raise ImportError("PyAnnote.audio not installed. Install with: pip install pyannote.audio")
        except Exception as e:
            raise Exception(f"Failed to load PyAnnote model: {e}")
    
    def _initialize_resemblyzer(self):
        """Initialize Resemblyzer for speaker embeddings"""
        try:
            from resemblyzer import VoiceEncoder, preprocess_wav
            
            self.model = VoiceEncoder()
            self.preprocess_wav = preprocess_wav
            log.debug("Resemblyzer voice encoder loaded")
            
        except ImportError:
            raise ImportError("Resemblyzer not installed. Install with: pip install resemblyzer")
    
    def _initialize_speechbrain(self):
        """Initialize SpeechBrain for speaker recognition"""
        try:
            from speechbrain.pretrained import SpeakerRecognition
            
            model_name = Config.SPEAKER_IDENTIFICATION.get("speechbrain_model", "speechbrain/spkrec-ecapa-voxceleb")
            self.model = SpeakerRecognition.from_hparams(source=model_name)
            log.debug("SpeechBrain speaker recognition model loaded")
            
        except ImportError:
            raise ImportError("SpeechBrain not installed. Install with: pip install speechbrain")
    
    def is_enabled(self) -> bool:
        """Check if speaker identification is enabled and working"""
        return self.enabled and self.initialized
    
    def identify_speakers(self, audio_data: np.ndarray, sample_rate: int, 
                         transcription_text: str = None) -> List[SpeakerSegment]:
        """
        Identify speakers in audio data
        
        Args:
            audio_data: Audio samples as numpy array
            sample_rate: Audio sample rate
            transcription_text: Optional transcription text for the audio
            
        Returns:
            List of speaker segments
        """
        if not self.is_enabled():
            # Return single segment with unknown speaker if disabled
            duration = len(audio_data) / sample_rate
            return [SpeakerSegment(
                start_time=0.0,
                end_time=duration,
                speaker_id="SPEAKER_UNKNOWN",
                confidence=1.0,
                text=transcription_text
            )]
        
        try:
            if self.method == SpeakerMethod.SIMPLE_ENERGY:
                return self._identify_speakers_simple_energy(audio_data, sample_rate, transcription_text)
            elif self.method == SpeakerMethod.PYANNOTE:
                return self._identify_speakers_pyannote(audio_data, sample_rate, transcription_text)
            elif self.method == SpeakerMethod.RESEMBLYZER:
                return self._identify_speakers_resemblyzer(audio_data, sample_rate, transcription_text)
            elif self.method == SpeakerMethod.SPEECHBRAIN:
                return self._identify_speakers_speechbrain(audio_data, sample_rate, transcription_text)
            else:
                log.warning(f"Speaker identification method {self.method.value} not implemented")
                return []
                
        except Exception as e:
            log.error(f"Error in speaker identification: {e}")
            # Return fallback segment
            duration = len(audio_data) / sample_rate
            return [SpeakerSegment(
                start_time=0.0,
                end_time=duration,
                speaker_id="SPEAKER_ERROR",
                confidence=0.0,
                text=transcription_text
            )]
    
    def _identify_speakers_simple_energy(self, audio_data: np.ndarray, sample_rate: int, 
                                       transcription_text: str = None) -> List[SpeakerSegment]:
        """Simple energy-based speaker change detection"""
        # Calculate energy levels
        window_size = int(sample_rate * 0.1)  # 100ms windows
        energy_levels = []
        
        for i in range(0, len(audio_data) - window_size, window_size):
            window = audio_data[i:i + window_size]
            energy = np.mean(window ** 2)
            energy_levels.append(energy)
        
        if not energy_levels:
            duration = len(audio_data) / sample_rate
            return [SpeakerSegment(0.0, duration, "SPEAKER_01", 0.8, transcription_text)]
        
        # Smooth energy levels
        smoothed_energy = self._smooth_signal(energy_levels, self.smoothing_window)
        
        # Detect speaker changes based on energy variations
        speaker_changes = self._detect_energy_changes(smoothed_energy)
        
        # Create speaker segments
        segments = []
        current_speaker = 1
        
        for i, change_point in enumerate(speaker_changes):
            start_time = change_point * 0.1  # Convert window index to seconds
            end_time = speaker_changes[i + 1] * 0.1 if i + 1 < len(speaker_changes) else len(audio_data) / sample_rate
            
            if end_time - start_time >= self.min_segment_duration:
                segments.append(SpeakerSegment(
                    start_time=start_time,
                    end_time=end_time,
                    speaker_id=f"SPEAKER_{current_speaker:02d}",
                    confidence=0.8,
                    text=transcription_text if len(segments) == 0 else None  # Only assign text to first segment
                ))
                current_speaker = (current_speaker % self.max_speakers) + 1
        
        return segments if segments else [SpeakerSegment(0.0, len(audio_data) / sample_rate, "SPEAKER_01", 0.8, transcription_text)]
    
    def _identify_speakers_pyannote(self, audio_data: np.ndarray, sample_rate: int, 
                                  transcription_text: str = None) -> List[SpeakerSegment]:
        """PyAnnote-based speaker diarization"""
        # Convert numpy array to format expected by PyAnnote
        import tempfile
        import soundfile as sf
        
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_file:
            sf.write(tmp_file.name, audio_data, sample_rate)
            
            # Run diarization
            diarization = self.model(tmp_file.name)
            
            # Convert to our format
            segments = []
            for turn, _, speaker in diarization.itertracks(yield_label=True):
                segments.append(SpeakerSegment(
                    start_time=turn.start,
                    end_time=turn.end,
                    speaker_id=f"SPEAKER_{speaker}",
                    confidence=0.9,
                    text=transcription_text if len(segments) == 0 else None
                ))
            
            # Clean up temp file
            os.unlink(tmp_file.name)
            
        return segments
    
    def _identify_speakers_resemblyzer(self, audio_data: np.ndarray, sample_rate: int, 
                                     transcription_text: str = None) -> List[SpeakerSegment]:
        """Resemblyzer-based speaker identification"""
        # Preprocess audio for Resemblyzer
        wav = self.preprocess_wav(audio_data, sample_rate)
        
        # Extract speaker embedding
        embedding = self.model.embed_utterance(wav)
        
        # Compare with known speaker profiles
        speaker_id, confidence = self._match_speaker_profile(embedding)
        
        duration = len(audio_data) / sample_rate
        return [SpeakerSegment(
            start_time=0.0,
            end_time=duration,
            speaker_id=speaker_id,
            confidence=confidence,
            text=transcription_text
        )]
    
    def _identify_speakers_speechbrain(self, audio_data: np.ndarray, sample_rate: int, 
                                     transcription_text: str = None) -> List[SpeakerSegment]:
        """SpeechBrain-based speaker recognition"""
        import tempfile
        import soundfile as sf
        
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_file:
            sf.write(tmp_file.name, audio_data, sample_rate)
            
            # Extract speaker embedding
            embedding = self.model.encode_batch(tmp_file.name)
            
            # Compare with known profiles
            speaker_id, confidence = self._match_speaker_profile(embedding.squeeze().numpy())
            
            # Clean up
            os.unlink(tmp_file.name)
        
        duration = len(audio_data) / sample_rate
        return [SpeakerSegment(
            start_time=0.0,
            end_time=duration,
            speaker_id=speaker_id,
            confidence=confidence,
            text=transcription_text
        )]
    
    def _smooth_signal(self, signal: List[float], window_size: int) -> List[float]:
        """Apply smoothing to signal"""
        if window_size <= 1:
            return signal
            
        smoothed = []
        for i in range(len(signal)):
            start = max(0, i - window_size // 2)
            end = min(len(signal), i + window_size // 2 + 1)
            smoothed.append(np.mean(signal[start:end]))
        
        return smoothed
    
    def _detect_energy_changes(self, energy_levels: List[float]) -> List[int]:
        """Detect speaker change points based on energy variations"""
        if len(energy_levels) < 3:
            return [0]
        
        changes = [0]  # Always start with first window
        
        # Look for significant energy changes
        for i in range(1, len(energy_levels) - 1):
            # Calculate local variance
            window = energy_levels[max(0, i-2):i+3]
            variance = np.var(window)
            
            # If variance is high, potential speaker change
            if variance > self.energy_threshold:
                # Ensure minimum distance between changes
                if not changes or i - changes[-1] > 10:  # At least 1 second apart
                    changes.append(i)
        
        return changes
    
    def _match_speaker_profile(self, embedding: np.ndarray) -> Tuple[str, float]:
        """Match embedding against known speaker profiles"""
        with self.lock:
            if not self.speaker_profiles:
                # Create new speaker profile
                speaker_id = f"SPEAKER_{len(self.speaker_profiles) + 1:02d}"
                profile = SpeakerProfile(
                    speaker_id=speaker_id,
                    name=None,
                    voice_features={"embedding": embedding.tolist()},
                    sample_count=1,
                    created_at=time.time(),
                    last_seen=time.time()
                )
                self.speaker_profiles[speaker_id] = profile
                return speaker_id, 0.9
            
            # Compare with existing profiles
            best_match = None
            best_similarity = 0.0
            
            for profile in self.speaker_profiles.values():
                stored_embedding = np.array(profile.voice_features["embedding"])
                similarity = self._calculate_similarity(embedding, stored_embedding)
                
                if similarity > best_similarity:
                    best_similarity = similarity
                    best_match = profile
            
            if best_match and best_similarity > self.confidence_threshold:
                # Update profile
                best_match.last_seen = time.time()
                best_match.sample_count += 1
                return best_match.speaker_id, best_similarity
            else:
                # Create new speaker
                speaker_id = f"SPEAKER_{len(self.speaker_profiles) + 1:02d}"
                profile = SpeakerProfile(
                    speaker_id=speaker_id,
                    name=None,
                    voice_features={"embedding": embedding.tolist()},
                    sample_count=1,
                    created_at=time.time(),
                    last_seen=time.time()
                )
                self.speaker_profiles[speaker_id] = profile
                return speaker_id, 0.8
    
    def _calculate_similarity(self, embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """Calculate cosine similarity between embeddings"""
        dot_product = np.dot(embedding1, embedding2)
        norm1 = np.linalg.norm(embedding1)
        norm2 = np.linalg.norm(embedding2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
            
        return dot_product / (norm1 * norm2)
    
    def add_speaker_segments(self, segments: List[SpeakerSegment]):
        """Add speaker segments to history"""
        with self.lock:
            self.segment_history.extend(segments)
            # Keep only recent segments (last 1000)
            if len(self.segment_history) > 1000:
                self.segment_history = self.segment_history[-1000:]
    
    def get_speaker_profiles(self) -> Dict[str, Dict[str, Any]]:
        """Get all speaker profiles"""
        with self.lock:
            return {sid: asdict(profile) for sid, profile in self.speaker_profiles.items()}
    
    def update_speaker_name(self, speaker_id: str, name: str) -> bool:
        """Update speaker name"""
        with self.lock:
            if speaker_id in self.speaker_profiles:
                self.speaker_profiles[speaker_id].name = name
                return True
            return False
    
    def remove_speaker_profile(self, speaker_id: str) -> bool:
        """Remove speaker profile"""
        with self.lock:
            if speaker_id in self.speaker_profiles:
                del self.speaker_profiles[speaker_id]
                return True
            return False
    
    def get_speaker_statistics(self) -> Dict[str, Any]:
        """Get speaker identification statistics"""
        with self.lock:
            total_segments = len(self.segment_history)
            speaker_counts = {}
            
            for segment in self.segment_history:
                speaker_counts[segment.speaker_id] = speaker_counts.get(segment.speaker_id, 0) + 1
            
            return {
                "enabled": self.enabled,
                "method": self.method.value,
                "total_segments": total_segments,
                "unique_speakers": len(self.speaker_profiles),
                "speaker_counts": speaker_counts,
                "confidence_threshold": self.confidence_threshold,
                "min_segment_duration": self.min_segment_duration
            }
    
    def enable(self, method: str = None):
        """Enable speaker identification"""
        if method:
            self.method = SpeakerMethod(method)
        self.enabled = True
        if not self.initialized:
            self._initialize_method()
        log.info(f"Speaker identification enabled with method: {self.method.value}")
    
    def disable(self):
        """Disable speaker identification"""
        self.enabled = False
        log.info("Speaker identification disabled")