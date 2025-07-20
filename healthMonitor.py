import time
import threading
import psutil
import os
from collections import deque
from dataclasses import dataclass, asdict
from typing import Optional, Dict, Any
from logger import log

@dataclass
class SystemMetrics:
    cpu_percent: float
    memory_percent: float
    memory_used_mb: float
    memory_total_mb: float
    disk_usage_percent: float
    process_threads: int
    process_memory_mb: float

@dataclass
class TranscriptionMetrics:
    total_chunks_processed: int
    successful_transcriptions: int
    failed_transcriptions: int
    api_requests_sent: int
    api_requests_failed: int
    average_processing_time_ms: float
    last_transcription_time: Optional[float]
    last_api_call_time: Optional[float]
    uptime_seconds: float

@dataclass
class ComponentStatus:
    audio_capture_active: bool
    audio_processor_active: bool
    whisper_service_active: bool
    api_service_active: bool
    pipeline_running: bool
    whisper_model_loaded: bool

@dataclass
class HealthStatus:
    status: str  # "healthy", "degraded", "unhealthy"
    timestamp: float
    uptime_seconds: float
    system_metrics: SystemMetrics
    transcription_metrics: TranscriptionMetrics
    component_status: ComponentStatus
    recent_errors: list
    performance_warnings: list

class HealthMonitor:
    def __init__(self, pipeline=None):
        self.pipeline = pipeline
        self.start_time = time.time()
        
        # Metrics tracking
        self.total_chunks_processed = 0
        self.successful_transcriptions = 0
        self.failed_transcriptions = 0
        self.api_requests_sent = 0
        self.api_requests_failed = 0
        self.processing_times = deque(maxlen=100)  # Keep last 100 processing times
        self.last_transcription_time = None
        self.last_api_call_time = None
        
        # Error tracking
        self.recent_errors = deque(maxlen=50)  # Keep last 50 errors
        self.performance_warnings = deque(maxlen=20)  # Keep last 20 warnings
        
        # Thread safety
        self.lock = threading.Lock()
        
        # Process info
        self.process = psutil.Process()
        
    def record_chunk_processed(self):
        with self.lock:
            self.total_chunks_processed += 1
            
    def record_transcription_success(self, processing_time_ms: float):
        with self.lock:
            self.successful_transcriptions += 1
            self.processing_times.append(processing_time_ms)
            self.last_transcription_time = time.time()
            
            # Check for performance warnings
            if processing_time_ms > 5000:  # > 5 seconds
                self.performance_warnings.append({
                    "timestamp": time.time(),
                    "type": "slow_transcription",
                    "message": f"Slow transcription: {processing_time_ms:.0f}ms",
                    "value": processing_time_ms
                })
                
    def record_transcription_failure(self, error: str):
        with self.lock:
            self.failed_transcriptions += 1
            self.recent_errors.append({
                "timestamp": time.time(),
                "type": "transcription_error",
                "message": error
            })
            
    def record_api_request_sent(self):
        with self.lock:
            self.api_requests_sent += 1
            self.last_api_call_time = time.time()
            
    def record_api_request_failed(self, error: str):
        with self.lock:
            self.api_requests_failed += 1
            self.recent_errors.append({
                "timestamp": time.time(),
                "type": "api_error", 
                "message": error
            })
            
    def record_error(self, error_type: str, message: str):
        with self.lock:
            self.recent_errors.append({
                "timestamp": time.time(),
                "type": error_type,
                "message": message
            })
            
    def get_system_metrics(self) -> SystemMetrics:
        try:
            # System-wide metrics
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # Process-specific metrics
            process_memory = self.process.memory_info()
            
            return SystemMetrics(
                cpu_percent=cpu_percent,
                memory_percent=memory.percent,
                memory_used_mb=memory.used / (1024 * 1024),
                memory_total_mb=memory.total / (1024 * 1024),
                disk_usage_percent=disk.percent,
                process_threads=self.process.num_threads(),
                process_memory_mb=process_memory.rss / (1024 * 1024)
            )
        except Exception as e:
            log.error(f"Error getting system metrics: {e}")
            return SystemMetrics(0, 0, 0, 0, 0, 0, 0)
            
    def get_transcription_metrics(self) -> TranscriptionMetrics:
        with self.lock:
            avg_processing_time = 0
            if self.processing_times:
                avg_processing_time = sum(self.processing_times) / len(self.processing_times)
                
            return TranscriptionMetrics(
                total_chunks_processed=self.total_chunks_processed,
                successful_transcriptions=self.successful_transcriptions,
                failed_transcriptions=self.failed_transcriptions,
                api_requests_sent=self.api_requests_sent,
                api_requests_failed=self.api_requests_failed,
                average_processing_time_ms=avg_processing_time,
                last_transcription_time=self.last_transcription_time,
                last_api_call_time=self.last_api_call_time,
                uptime_seconds=time.time() - self.start_time
            )
            
    def get_component_status(self) -> ComponentStatus:
        if not self.pipeline:
            return ComponentStatus(False, False, False, False, False, False)
            
        try:
            # Check if Whisper model exists
            whisper_model_loaded = False
            if hasattr(self.pipeline, 'whisper_service'):
                model_path = self.pipeline.whisper_service.config.WHISPER["model_path"]
                whisper_model_loaded = os.path.exists(model_path)
                
            return ComponentStatus(
                audio_capture_active=hasattr(self.pipeline.audio_capture, 'stream') and 
                                   self.pipeline.audio_capture.stream is not None and
                                   self.pipeline.audio_capture.stream.active,
                audio_processor_active=self.pipeline.is_running,
                whisper_service_active=hasattr(self.pipeline, 'whisper_service'),
                api_service_active=hasattr(self.pipeline, 'api_service'),
                pipeline_running=self.pipeline.is_running,
                whisper_model_loaded=whisper_model_loaded
            )
        except Exception as e:
            log.error(f"Error getting component status: {e}")
            return ComponentStatus(False, False, False, False, False, False)
            
    def determine_health_status(self, system_metrics: SystemMetrics, 
                              transcription_metrics: TranscriptionMetrics,
                              component_status: ComponentStatus) -> str:
        # Critical issues
        if not component_status.pipeline_running:
            return "unhealthy"
            
        if not component_status.whisper_model_loaded:
            return "unhealthy"
            
        # Resource issues
        if system_metrics.cpu_percent > 90 or system_metrics.memory_percent > 90:
            return "degraded"
            
        # Performance issues
        if (transcription_metrics.failed_transcriptions > 0 and 
            transcription_metrics.total_chunks_processed > 0):
            failure_rate = transcription_metrics.failed_transcriptions / transcription_metrics.total_chunks_processed
            if failure_rate > 0.5:  # More than 50% failure rate
                return "degraded"
                
        # API issues
        if (transcription_metrics.api_requests_failed > 0 and 
            transcription_metrics.api_requests_sent > 0):
            api_failure_rate = transcription_metrics.api_requests_failed / transcription_metrics.api_requests_sent
            if api_failure_rate > 0.3:  # More than 30% API failure rate
                return "degraded"
                
        # Check for recent activity
        current_time = time.time()
        if (transcription_metrics.last_transcription_time and 
            current_time - transcription_metrics.last_transcription_time > 300):  # 5 minutes
            return "degraded"
            
        return "healthy"
        
    def get_health_status(self) -> HealthStatus:
        system_metrics = self.get_system_metrics()
        transcription_metrics = self.get_transcription_metrics()
        component_status = self.get_component_status()
        
        health_status = self.determine_health_status(
            system_metrics, transcription_metrics, component_status
        )
        
        with self.lock:
            recent_errors = list(self.recent_errors)
            performance_warnings = list(self.performance_warnings)
            
        return HealthStatus(
            status=health_status,
            timestamp=time.time(),
            uptime_seconds=time.time() - self.start_time,
            system_metrics=system_metrics,
            transcription_metrics=transcription_metrics,
            component_status=component_status,
            recent_errors=recent_errors,
            performance_warnings=performance_warnings
        )
        
    def get_health_summary(self) -> Dict[str, Any]:
        health_status = self.get_health_status()
        return {
            "status": health_status.status,
            "timestamp": health_status.timestamp,
            "uptime_seconds": health_status.uptime_seconds,
            "summary": {
                "pipeline_running": health_status.component_status.pipeline_running,
                "total_transcriptions": health_status.transcription_metrics.successful_transcriptions,
                "cpu_usage": health_status.system_metrics.cpu_percent,
                "memory_usage": health_status.system_metrics.memory_percent,
                "recent_errors_count": len(health_status.recent_errors),
                "api_success_rate": self._calculate_api_success_rate(health_status.transcription_metrics)
            }
        }
        
    def _calculate_api_success_rate(self, metrics: TranscriptionMetrics) -> float:
        if metrics.api_requests_sent == 0:
            return 0.0
        return ((metrics.api_requests_sent - metrics.api_requests_failed) / 
                metrics.api_requests_sent) * 100