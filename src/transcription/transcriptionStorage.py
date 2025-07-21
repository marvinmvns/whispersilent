import json
import time
import threading
from collections import deque
from dataclasses import dataclass, asdict
from typing import List, Optional, Dict, Any
from logger import log

@dataclass
class TranscriptionRecord:
    id: str
    text: str
    timestamp: float
    processing_time_ms: float
    chunk_size: int
    api_sent: bool
    api_sent_timestamp: Optional[float] = None
    confidence: Optional[float] = None
    language: Optional[str] = None

class TranscriptionStorage:
    def __init__(self, max_records: int = 1000):
        self.max_records = max_records
        self.records = deque(maxlen=max_records)
        self.lock = threading.Lock()
        self.record_counter = 0
        
    def add_transcription(self, text: str, processing_time_ms: float, 
                         chunk_size: int, api_sent: bool = False,
                         confidence: Optional[float] = None,
                         language: Optional[str] = None) -> str:
        """Add a new transcription record and return its ID"""
        with self.lock:
            self.record_counter += 1
            record_id = f"trans_{int(time.time())}_{self.record_counter}"
            
            record = TranscriptionRecord(
                id=record_id,
                text=text,
                timestamp=time.time(),
                processing_time_ms=processing_time_ms,
                chunk_size=chunk_size,
                api_sent=api_sent,
                api_sent_timestamp=time.time() if api_sent else None,
                confidence=confidence,
                language=language
            )
            
            self.records.append(record)
            log.debug(f"Stored transcription record: {record_id}")
            return record_id
            
    def mark_api_sent(self, record_id: str) -> bool:
        """Mark a transcription as sent to API"""
        with self.lock:
            for record in self.records:
                if record.id == record_id:
                    record.api_sent = True
                    record.api_sent_timestamp = time.time()
                    return True
            return False
            
    def get_all_transcriptions(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get all transcriptions, optionally limited"""
        with self.lock:
            records = list(self.records)
            
        if limit:
            records = records[-limit:]  # Get the most recent records
            
        return [asdict(record) for record in records]
        
    def get_transcriptions_by_timerange(self, start_time: float, 
                                      end_time: float) -> List[Dict[str, Any]]:
        """Get transcriptions within a time range"""
        with self.lock:
            filtered_records = [
                record for record in self.records
                if start_time <= record.timestamp <= end_time
            ]
            
        return [asdict(record) for record in filtered_records]
        
    def get_transcription_by_id(self, record_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific transcription by ID"""
        with self.lock:
            for record in self.records:
                if record.id == record_id:
                    return asdict(record)
            return None
            
    def get_recent_transcriptions(self, minutes: int = 60) -> List[Dict[str, Any]]:
        """Get transcriptions from the last N minutes"""
        cutoff_time = time.time() - (minutes * 60)
        return self.get_transcriptions_by_timerange(cutoff_time, time.time())
        
    def get_unsent_transcriptions(self) -> List[Dict[str, Any]]:
        """Get transcriptions that haven't been sent to API"""
        with self.lock:
            unsent_records = [
                record for record in self.records
                if not record.api_sent
            ]
            
        return [asdict(record) for record in unsent_records]
        
    def search_transcriptions(self, query: str, case_sensitive: bool = False) -> List[Dict[str, Any]]:
        """Search transcriptions by text content"""
        with self.lock:
            if case_sensitive:
                matching_records = [
                    record for record in self.records
                    if query in record.text
                ]
            else:
                query_lower = query.lower()
                matching_records = [
                    record for record in self.records
                    if query_lower in record.text.lower()
                ]
                
        return [asdict(record) for record in matching_records]
        
    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about stored transcriptions"""
        with self.lock:
            records = list(self.records)
            
        if not records:
            return {
                "total_records": 0,
                "sent_to_api": 0,
                "average_processing_time_ms": 0,
                "oldest_timestamp": None,
                "newest_timestamp": None,
                "total_characters": 0
            }
            
        sent_count = sum(1 for r in records if r.api_sent)
        avg_processing_time = sum(r.processing_time_ms for r in records) / len(records)
        total_chars = sum(len(r.text) for r in records)
        
        return {
            "total_records": len(records),
            "sent_to_api": sent_count,
            "pending_api_send": len(records) - sent_count,
            "average_processing_time_ms": round(avg_processing_time, 2),
            "oldest_timestamp": records[0].timestamp if records else None,
            "newest_timestamp": records[-1].timestamp if records else None,
            "total_characters": total_chars,
            "api_send_rate": round((sent_count / len(records)) * 100, 2) if records else 0
        }
        
    def export_to_json(self, filename: Optional[str] = None) -> str:
        """Export all transcriptions to a JSON file"""
        if not filename:
            filename = f"transcriptions_export_{int(time.time())}.json"
            
        data = {
            "export_timestamp": time.time(),
            "total_records": len(self.records),
            "transcriptions": self.get_all_transcriptions()
        }
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            log.info(f"Transcriptions exported to {filename}")
            return filename
        except Exception as e:
            log.error(f"Error exporting transcriptions: {e}")
            raise
            
    def clear_old_records(self, days: int = 7):
        """Clear records older than specified days"""
        cutoff_time = time.time() - (days * 24 * 60 * 60)
        
        with self.lock:
            original_count = len(self.records)
            # Convert to list, filter, and recreate deque
            recent_records = [r for r in self.records if r.timestamp >= cutoff_time]
            self.records.clear()
            self.records.extend(recent_records)
            
            removed_count = original_count - len(self.records)
            if removed_count > 0:
                log.info(f"Cleared {removed_count} old transcription records (older than {days} days)")
                
    def get_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get a summary of transcriptions for the last N hours"""
        cutoff_time = time.time() - (hours * 60 * 60)
        recent_records = [
            record for record in self.records
            if record.timestamp >= cutoff_time
        ]
        
        if not recent_records:
            return {
                "period_hours": hours,
                "total_transcriptions": 0,
                "total_characters": 0,
                "average_processing_time_ms": 0,
                "api_success_rate": 0
            }
            
        total_chars = sum(len(r.text) for r in recent_records)
        avg_processing = sum(r.processing_time_ms for r in recent_records) / len(recent_records)
        api_sent = sum(1 for r in recent_records if r.api_sent)
        
        return {
            "period_hours": hours,
            "total_transcriptions": len(recent_records),
            "total_characters": total_chars,
            "average_processing_time_ms": round(avg_processing, 2),
            "api_success_rate": round((api_sent / len(recent_records)) * 100, 2),
            "transcriptions_per_hour": round(len(recent_records) / hours, 2)
        }