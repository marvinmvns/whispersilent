import time
import threading
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
from logger import log
from config import Config

@dataclass
class AggregatedText:
    """Represents an aggregated text block for an hour"""
    hour_timestamp: float  # Unix timestamp for the start of the hour
    start_time: float      # First transcription timestamp
    end_time: float        # Last transcription timestamp
    full_text: str         # Complete aggregated text
    transcription_count: int  # Number of individual transcriptions
    silence_gaps: List[Dict[str, float]]  # List of silence periods
    metadata: Dict[str, Any]  # Additional metadata
    sent_to_api: bool = False
    created_at: float = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = time.time()

class HourlyAggregator:
    """
    Service that aggregates transcription texts on an hourly basis.
    
    Features:
    - Collects individual transcriptions during an hour
    - Detects 5+ minute silence gaps between transcriptions
    - Sends aggregated text to API after each hour or after silence gap
    - Allows partial queries during aggregation period
    - Maintains history of aggregated texts
    """
    
    def __init__(self, api_service=None, min_silence_gap_minutes=5):
        self.api_service = api_service
        self.min_silence_gap_minutes = min_silence_gap_minutes
        self.min_silence_gap_seconds = min_silence_gap_minutes * 60
        
        # Current hour's data
        self.current_hour_start = None
        self.current_transcriptions = []
        self.current_text_parts = []
        self.last_transcription_time = None
        
        # Aggregated history
        self.aggregated_texts = []
        self.lock = threading.Lock()
        
        # Control flags
        self.enabled = True
        self.running = False
        
        # Background thread for periodic checks
        self.check_thread = None
        self.stop_event = threading.Event()
        
        log.info(f"HourlyAggregator initialized with {min_silence_gap_minutes}-minute silence detection")
    
    def start(self):
        """Start the hourly aggregator service"""
        if self.running:
            return
            
        self.running = True
        self.stop_event.clear()
        
        # Start background thread for periodic checks
        self.check_thread = threading.Thread(target=self._periodic_check, daemon=True)
        self.check_thread.start()
        
        log.info("HourlyAggregator service started")
    
    def stop(self):
        """Stop the hourly aggregator service"""
        if not self.running:
            return
            
        self.running = False
        self.stop_event.set()
        
        # Finalize any pending aggregation
        self._finalize_current_hour("Service stopped")
        
        if self.check_thread and self.check_thread.is_alive():
            self.check_thread.join(timeout=2)
            
        log.info("HourlyAggregator service stopped")
    
    def add_transcription(self, transcription_text: str, timestamp: float = None, metadata: Dict[str, Any] = None):
        """
        Add a new transcription to the current hour's collection
        
        Args:
            transcription_text: The transcribed text
            timestamp: Unix timestamp (defaults to current time)
            metadata: Additional metadata for this transcription
        """
        if not self.enabled:
            log.debug("HourlyAggregator is disabled, skipping transcription")
            return
            
        if timestamp is None:
            timestamp = time.time()
            
        if metadata is None:
            metadata = {}
        
        with self.lock:
            # Check if we need to start a new hour
            current_hour = self._get_hour_start(timestamp)
            
            # If this is the first transcription or we've moved to a new hour
            if self.current_hour_start is None:
                self._start_new_hour(current_hour, timestamp)
            elif current_hour != self.current_hour_start:
                # Finalize the previous hour and start new one
                self._finalize_current_hour("New hour started")
                self._start_new_hour(current_hour, timestamp)
            
            # Check for silence gap if we have previous transcriptions
            if self.last_transcription_time is not None:
                silence_duration = timestamp - self.last_transcription_time
                if silence_duration >= self.min_silence_gap_seconds:
                    log.info(f"Detected {silence_duration/60:.1f}-minute silence gap, finalizing current aggregation")
                    self._finalize_current_hour(f"Silence gap of {silence_duration/60:.1f} minutes")
                    self._start_new_hour(current_hour, timestamp)
            
            # Add the transcription to current collection
            transcription_data = {
                "text": transcription_text,
                "timestamp": timestamp,
                "metadata": metadata
            }
            
            self.current_transcriptions.append(transcription_data)
            self.current_text_parts.append(transcription_text.strip())
            self.last_transcription_time = timestamp
            
            log.debug(f"Added transcription to hour {datetime.fromtimestamp(current_hour).strftime('%Y-%m-%d %H:00')} "
                     f"(total: {len(self.current_transcriptions)} transcriptions)")
    
    def get_current_partial_text(self) -> Optional[str]:
        """Get the current partial aggregated text for the ongoing hour"""
        with self.lock:
            if not self.current_text_parts:
                return None
                
            return " ".join(self.current_text_parts)
    
    def get_current_status(self) -> Dict[str, Any]:
        """Get current aggregation status"""
        with self.lock:
            current_partial = self.get_current_partial_text()
            
            return {
                "enabled": self.enabled,
                "running": self.running,
                "current_hour_start": self.current_hour_start,
                "current_hour_formatted": datetime.fromtimestamp(self.current_hour_start).strftime('%Y-%m-%d %H:00') if self.current_hour_start else None,
                "current_transcription_count": len(self.current_transcriptions),
                "current_partial_text": current_partial,
                "current_partial_length": len(current_partial) if current_partial else 0,
                "last_transcription_time": self.last_transcription_time,
                "last_transcription_formatted": datetime.fromtimestamp(self.last_transcription_time).strftime('%Y-%m-%d %H:%M:%S') if self.last_transcription_time else None,
                "minutes_since_last": (time.time() - self.last_transcription_time) / 60 if self.last_transcription_time else None,
                "total_aggregated_hours": len(self.aggregated_texts),
                "min_silence_gap_minutes": self.min_silence_gap_minutes
            }
    
    def get_aggregated_texts(self, limit: int = None) -> List[Dict[str, Any]]:
        """Get list of completed aggregated texts"""
        with self.lock:
            texts = [asdict(text) for text in self.aggregated_texts]
            if limit:
                texts = texts[-limit:]
            return texts
    
    def get_aggregated_text_by_hour(self, hour_timestamp: float) -> Optional[Dict[str, Any]]:
        """Get aggregated text for a specific hour"""
        with self.lock:
            for text in self.aggregated_texts:
                if text.hour_timestamp == hour_timestamp:
                    return asdict(text)
            return None
    
    def force_finalize_current(self, reason: str = "Manual trigger") -> Optional[Dict[str, Any]]:
        """Force finalization of the current hour's aggregation"""
        with self.lock:
            if not self.current_transcriptions:
                log.warning("No current transcriptions to finalize")
                return None
                
            aggregated = self._finalize_current_hour(reason)
            return asdict(aggregated) if aggregated else None
    
    def set_enabled(self, enabled: bool):
        """Enable or disable the aggregator"""
        self.enabled = enabled
        log.info(f"HourlyAggregator {'enabled' if enabled else 'disabled'}")
    
    def _get_hour_start(self, timestamp: float) -> float:
        """Get the start timestamp of the hour containing the given timestamp"""
        dt = datetime.fromtimestamp(timestamp)
        hour_start = dt.replace(minute=0, second=0, microsecond=0)
        return hour_start.timestamp()
    
    def _start_new_hour(self, hour_start: float, first_timestamp: float):
        """Start collecting transcriptions for a new hour"""
        self.current_hour_start = hour_start
        self.current_transcriptions = []
        self.current_text_parts = []
        
        hour_formatted = datetime.fromtimestamp(hour_start).strftime('%Y-%m-%d %H:00')
        log.info(f"Started new aggregation period for hour: {hour_formatted}")
    
    def _finalize_current_hour(self, reason: str) -> Optional[AggregatedText]:
        """Finalize the current hour's aggregation and optionally send to API"""
        if not self.current_transcriptions:
            log.debug("No transcriptions to finalize")
            return None
        
        # Calculate silence gaps
        silence_gaps = []
        for i in range(1, len(self.current_transcriptions)):
            prev_time = self.current_transcriptions[i-1]["timestamp"]
            curr_time = self.current_transcriptions[i]["timestamp"]
            gap_duration = curr_time - prev_time
            
            if gap_duration > 30:  # Only record gaps longer than 30 seconds
                silence_gaps.append({
                    "start_time": prev_time,
                    "end_time": curr_time,
                    "duration_seconds": gap_duration,
                    "duration_minutes": gap_duration / 60
                })
        
        # Create aggregated text
        full_text = " ".join(self.current_text_parts)
        start_time = self.current_transcriptions[0]["timestamp"]
        end_time = self.current_transcriptions[-1]["timestamp"]
        
        aggregated = AggregatedText(
            hour_timestamp=self.current_hour_start,
            start_time=start_time,
            end_time=end_time,
            full_text=full_text,
            transcription_count=len(self.current_transcriptions),
            silence_gaps=silence_gaps,
            metadata={
                "finalization_reason": reason,
                "total_duration_minutes": (end_time - start_time) / 60,
                "average_gap_seconds": sum(gap["duration_seconds"] for gap in silence_gaps) / len(silence_gaps) if silence_gaps else 0,
                "word_count": len(full_text.split()),
                "character_count": len(full_text)
            }
        )
        
        # Add to history
        self.aggregated_texts.append(aggregated)
        
        hour_formatted = datetime.fromtimestamp(self.current_hour_start).strftime('%Y-%m-%d %H:00')
        duration_minutes = (end_time - start_time) / 60
        
        log.info(f"Finalized aggregation for {hour_formatted}: {len(self.current_transcriptions)} transcriptions, "
                f"{len(full_text)} chars, {duration_minutes:.1f} minutes duration. Reason: {reason}")
        
        # Send to API if service is available
        if self.api_service and hasattr(self.api_service, 'send_transcription'):
            try:
                self.api_service.send_transcription(
                    full_text,
                    {
                        "aggregationType": "hourly",
                        "hourTimestamp": self.current_hour_start,
                        "transcriptionCount": len(self.current_transcriptions),
                        "durationMinutes": duration_minutes,
                        "silenceGaps": len(silence_gaps),
                        "finalizationReason": reason,
                        "wordCount": aggregated.metadata["word_count"],
                        "characterCount": aggregated.metadata["character_count"]
                    }
                )
                aggregated.sent_to_api = True
                log.info(f"Aggregated text sent to API successfully for {hour_formatted}")
            except Exception as e:
                log.error(f"Failed to send aggregated text to API for {hour_formatted}: {e}")
        
        # Clear current data
        self.current_hour_start = None
        self.current_transcriptions = []
        self.current_text_parts = []
        
        return aggregated
    
    def _periodic_check(self):
        """Background thread that periodically checks for conditions requiring finalization"""
        while self.running and not self.stop_event.wait(60):  # Check every minute
            try:
                with self.lock:
                    if not self.current_transcriptions:
                        continue
                    
                    current_time = time.time()
                    
                    # Check if we should finalize due to new hour
                    if self.current_hour_start:
                        current_hour = self._get_hour_start(current_time)
                        if current_hour != self.current_hour_start:
                            log.info("Hour boundary reached, finalizing current aggregation")
                            self._finalize_current_hour("Hour boundary reached")
                            continue
                    
                    # Check for extended silence
                    if self.last_transcription_time:
                        silence_duration = current_time - self.last_transcription_time
                        if silence_duration >= self.min_silence_gap_seconds:
                            log.info(f"Extended silence detected ({silence_duration/60:.1f} minutes), finalizing current aggregation")
                            self._finalize_current_hour(f"Extended silence: {silence_duration/60:.1f} minutes")
                            
            except Exception as e:
                log.error(f"Error in HourlyAggregator periodic check: {e}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get aggregation statistics"""
        with self.lock:
            total_aggregations = len(self.aggregated_texts)
            total_transcriptions = sum(text.transcription_count for text in self.aggregated_texts)
            total_characters = sum(len(text.full_text) for text in self.aggregated_texts)
            
            sent_to_api = sum(1 for text in self.aggregated_texts if text.sent_to_api)
            
            avg_transcriptions_per_hour = total_transcriptions / total_aggregations if total_aggregations > 0 else 0
            avg_characters_per_hour = total_characters / total_aggregations if total_aggregations > 0 else 0
            
            return {
                "total_aggregated_hours": total_aggregations,
                "total_transcriptions_aggregated": total_transcriptions,
                "total_characters_aggregated": total_characters,
                "sent_to_api_count": sent_to_api,
                "pending_api_send": total_aggregations - sent_to_api,
                "average_transcriptions_per_hour": avg_transcriptions_per_hour,
                "average_characters_per_hour": avg_characters_per_hour,
                "current_period_transcriptions": len(self.current_transcriptions),
                "current_period_characters": len(self.get_current_partial_text() or ""),
                "enabled": self.enabled,
                "running": self.running
            }