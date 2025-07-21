import os
import json
import time
import threading
from datetime import datetime
from typing import List, Dict, Any, Optional
from logger import log

class TranscriptionFileManager:
    def __init__(self, storage_dir: str = "transcriptions"):
        self.storage_dir = os.path.abspath(storage_dir)
        self.lock = threading.Lock()
        self._ensure_directories()
        
    def _ensure_directories(self):
        """Create necessary directories"""
        directories = [
            self.storage_dir,
            os.path.join(self.storage_dir, "daily"),
            os.path.join(self.storage_dir, "sessions"),
            os.path.join(self.storage_dir, "exports")
        ]
        
        for directory in directories:
            os.makedirs(directory, exist_ok=True)
            
    def _get_session_filename(self) -> str:
        """Get filename for current session"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"session_{timestamp}.json"
        
    def _get_daily_filename(self, date: Optional[datetime] = None) -> str:
        """Get filename for daily transcriptions"""
        if date is None:
            date = datetime.now()
        return f"transcriptions_{date.strftime('%Y%m%d')}.json"
        
    def save_session_transcriptions(self, transcriptions: List[Dict[str, Any]], 
                                  session_metadata: Optional[Dict[str, Any]] = None) -> str:
        """Save transcriptions for current session"""
        with self.lock:
            filename = self._get_session_filename()
            filepath = os.path.join(self.storage_dir, "sessions", filename)
            
            # Prepare session data
            session_data = {
                "session_metadata": session_metadata or {},
                "created_at": time.time(),
                "total_transcriptions": len(transcriptions),
                "transcriptions": sorted(transcriptions, key=lambda x: x.get('timestamp', 0))
            }
            
            # Add session summary
            if transcriptions:
                session_data["session_summary"] = {
                    "duration_seconds": transcriptions[-1].get('timestamp', 0) - transcriptions[0].get('timestamp', 0),
                    "total_characters": sum(len(t.get('text', '')) for t in transcriptions),
                    "average_processing_time_ms": sum(t.get('processing_time_ms', 0) for t in transcriptions) / len(transcriptions),
                    "first_transcription": transcriptions[0].get('timestamp', 0),
                    "last_transcription": transcriptions[-1].get('timestamp', 0)
                }
                
            try:
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(session_data, f, indent=2, ensure_ascii=False)
                    
                log.info(f"Session transcriptions saved to {filepath}")
                return filepath
                
            except Exception as e:
                log.error(f"Error saving session transcriptions: {e}")
                raise
                
    def append_to_daily_file(self, transcription: Dict[str, Any]) -> str:
        """Append transcription to daily file"""
        with self.lock:
            date = datetime.fromtimestamp(transcription.get('timestamp', time.time()))
            filename = self._get_daily_filename(date)
            filepath = os.path.join(self.storage_dir, "daily", filename)
            
            # Enhanced file operation logging
            file_exists = os.path.exists(filepath)
            
            # Load existing data or create new
            daily_data = {
                "date": date.strftime("%Y-%m-%d"),
                "transcriptions": []
            }
            
            if file_exists:
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        daily_data = json.load(f)
                    existing_count = len(daily_data.get('transcriptions', []))
                    print(f"📄 [JSON] Arquivo existente: {existing_count} transcrições")
                except Exception as e:
                    print(f"⚠️  [JSON] Erro lendo arquivo existente: {e}")
                    log.warning(f"Error reading existing daily file {filepath}: {e}")
            else:
                print(f"📄 [JSON] Criando novo arquivo: {filename}")
                    
            # Add new transcription
            daily_data["transcriptions"].append(transcription)
            
            # Sort by timestamp to maintain chronological order
            daily_data["transcriptions"].sort(key=lambda x: x.get('timestamp', 0))
            
            # Update metadata
            daily_data["last_updated"] = time.time()
            daily_data["total_transcriptions"] = len(daily_data["transcriptions"])
            
            # Calculate additional stats for logging
            total_chars = sum(len(t.get('text', '')) for t in daily_data["transcriptions"])
            api_sent_count = sum(1 for t in daily_data["transcriptions"] if t.get('api_sent', False))
            
            try:
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(daily_data, f, indent=2, ensure_ascii=False)
                
                # Enhanced success logging with file statistics
                file_size = os.path.getsize(filepath)
                print(f"💾 [JSON FILE] ✅ Salvo: {daily_data['total_transcriptions']} transcrições")
                print(f"    📊 Stats: {total_chars} chars | {api_sent_count}/{daily_data['total_transcriptions']} enviadas p/ API")
                print(f"    📦 Arquivo: {file_size} bytes | {filepath}")
                
                log.info(f"Transcription appended to daily file: {filepath} (total: {daily_data['total_transcriptions']})")
                return filepath
                
            except Exception as e:
                print(f"🚨 [JSON ERROR] Falha ao salvar arquivo: {e}")
                log.error(f"Error appending to daily file: {e}")
                raise
                
    def create_chronological_export(self, start_time: float, end_time: float, 
                                  export_name: Optional[str] = None) -> str:
        """Create a chronologically ordered export of transcriptions"""
        if export_name is None:
            start_date = datetime.fromtimestamp(start_time).strftime("%Y%m%d")
            end_date = datetime.fromtimestamp(end_time).strftime("%Y%m%d")
            export_name = f"export_{start_date}_to_{end_date}"
            
        export_filepath = os.path.join(self.storage_dir, "exports", f"{export_name}.json")
        
        # Collect all transcriptions in time range from daily files
        all_transcriptions = []
        
        # Get all daily files that might contain transcriptions in the range
        daily_dir = os.path.join(self.storage_dir, "daily")
        if os.path.exists(daily_dir):
            for filename in os.listdir(daily_dir):
                if filename.endswith('.json'):
                    filepath = os.path.join(daily_dir, filename)
                    try:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            daily_data = json.load(f)
                            
                        # Filter transcriptions in time range
                        for transcription in daily_data.get('transcriptions', []):
                            timestamp = transcription.get('timestamp', 0)
                            if start_time <= timestamp <= end_time:
                                all_transcriptions.append(transcription)
                                
                    except Exception as e:
                        log.warning(f"Error reading daily file {filepath}: {e}")
                        
        # Sort chronologically
        all_transcriptions.sort(key=lambda x: x.get('timestamp', 0))
        
        # Create export data
        export_data = {
            "export_metadata": {
                "created_at": time.time(),
                "start_time": start_time,
                "end_time": end_time,
                "start_date": datetime.fromtimestamp(start_time).isoformat(),
                "end_date": datetime.fromtimestamp(end_time).isoformat(),
                "total_transcriptions": len(all_transcriptions)
            },
            "transcriptions": all_transcriptions
        }
        
        # Add summary statistics
        if all_transcriptions:
            export_data["summary"] = {
                "duration_seconds": end_time - start_time,
                "total_characters": sum(len(t.get('text', '')) for t in all_transcriptions),
                "average_processing_time_ms": sum(t.get('processing_time_ms', 0) for t in all_transcriptions) / len(all_transcriptions),
                "api_sent_count": sum(1 for t in all_transcriptions if t.get('api_sent', False)),
                "api_success_rate": (sum(1 for t in all_transcriptions if t.get('api_sent', False)) / len(all_transcriptions)) * 100
            }
            
        try:
            with open(export_filepath, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
                
            log.info(f"Chronological export created: {export_filepath}")
            return export_filepath
            
        except Exception as e:
            log.error(f"Error creating chronological export: {e}")
            raise
            
    def create_readable_transcript(self, start_time: float, end_time: float,
                                 output_name: Optional[str] = None) -> str:
        """Create a human-readable transcript file"""
        if output_name is None:
            start_date = datetime.fromtimestamp(start_time).strftime("%Y%m%d")
            end_date = datetime.fromtimestamp(end_time).strftime("%Y%m%d")
            output_name = f"transcript_{start_date}_to_{end_date}"
            
        transcript_filepath = os.path.join(self.storage_dir, "exports", f"{output_name}.txt")
        
        # Get chronologically ordered transcriptions
        export_filepath = self.create_chronological_export(start_time, end_time, f"temp_{output_name}")
        
        try:
            with open(export_filepath, 'r', encoding='utf-8') as f:
                export_data = json.load(f)
                
            transcriptions = export_data.get('transcriptions', [])
            
            # Create readable transcript
            with open(transcript_filepath, 'w', encoding='utf-8') as f:
                # Write header
                f.write("TRANSCRIÇÃO DE ÁUDIO\n")
                f.write("=" * 50 + "\n\n")
                f.write(f"Período: {datetime.fromtimestamp(start_time).strftime('%d/%m/%Y %H:%M:%S')} ")
                f.write(f"até {datetime.fromtimestamp(end_time).strftime('%d/%m/%Y %H:%M:%S')}\n")
                f.write(f"Total de transcrições: {len(transcriptions)}\n\n")
                
                # Write transcriptions with timestamps
                for i, transcription in enumerate(transcriptions, 1):
                    timestamp = transcription.get('timestamp', 0)
                    text = transcription.get('text', '')
                    dt = datetime.fromtimestamp(timestamp)
                    
                    f.write(f"[{i:03d}] {dt.strftime('%H:%M:%S')} - {text}\n")
                    
                # Write summary
                f.write("\n" + "=" * 50 + "\n")
                f.write("RESUMO\n")
                f.write("-" * 20 + "\n")
                
                if transcriptions:
                    total_chars = sum(len(t.get('text', '')) for t in transcriptions)
                    duration = end_time - start_time
                    
                    f.write(f"Duração total: {duration/60:.1f} minutos\n")
                    f.write(f"Total de caracteres: {total_chars}\n")
                    f.write(f"Média de caracteres por transcrição: {total_chars/len(transcriptions):.1f}\n")
                    
            # Clean up temporary export file
            os.remove(export_filepath)
            
            log.info(f"Readable transcript created: {transcript_filepath}")
            return transcript_filepath
            
        except Exception as e:
            log.error(f"Error creating readable transcript: {e}")
            raise
            
    def get_daily_files_list(self) -> List[Dict[str, Any]]:
        """Get list of available daily files"""
        daily_dir = os.path.join(self.storage_dir, "daily")
        files = []
        
        if os.path.exists(daily_dir):
            for filename in sorted(os.listdir(daily_dir)):
                if filename.endswith('.json'):
                    filepath = os.path.join(daily_dir, filename)
                    try:
                        stat = os.stat(filepath)
                        with open(filepath, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            
                        files.append({
                            "filename": filename,
                            "filepath": filepath,
                            "date": data.get('date'),
                            "total_transcriptions": data.get('total_transcriptions', 0),
                            "file_size_bytes": stat.st_size,
                            "last_modified": stat.st_mtime
                        })
                        
                    except Exception as e:
                        log.warning(f"Error reading daily file info {filepath}: {e}")
                        
        return files
        
    def cleanup_old_files(self, days_to_keep: int = 30):
        """Clean up old daily files"""
        cutoff_time = time.time() - (days_to_keep * 24 * 60 * 60)
        daily_dir = os.path.join(self.storage_dir, "daily")
        
        if not os.path.exists(daily_dir):
            return
            
        removed_count = 0
        for filename in os.listdir(daily_dir):
            if filename.endswith('.json'):
                filepath = os.path.join(daily_dir, filename)
                try:
                    stat = os.stat(filepath)
                    if stat.st_mtime < cutoff_time:
                        os.remove(filepath)
                        removed_count += 1
                        log.info(f"Removed old daily file: {filename}")
                        
                except Exception as e:
                    log.warning(f"Error removing old file {filepath}: {e}")
                    
        if removed_count > 0:
            log.info(f"Cleaned up {removed_count} old daily files (older than {days_to_keep} days)")
            
    def get_storage_statistics(self) -> Dict[str, Any]:
        """Get statistics about stored files"""
        stats = {
            "storage_directory": self.storage_dir,
            "daily_files": 0,
            "session_files": 0,
            "export_files": 0,
            "total_size_bytes": 0,
            "oldest_file": None,
            "newest_file": None
        }
        
        # Check each subdirectory
        for subdir, key in [("daily", "daily_files"), ("sessions", "session_files"), ("exports", "export_files")]:
            subdir_path = os.path.join(self.storage_dir, subdir)
            if os.path.exists(subdir_path):
                for filename in os.listdir(subdir_path):
                    if filename.endswith('.json') or filename.endswith('.txt'):
                        filepath = os.path.join(subdir_path, filename)
                        try:
                            stat = os.stat(filepath)
                            stats[key] += 1
                            stats["total_size_bytes"] += stat.st_size
                            
                            if stats["oldest_file"] is None or stat.st_mtime < stats["oldest_file"]:
                                stats["oldest_file"] = stat.st_mtime
                                
                            if stats["newest_file"] is None or stat.st_mtime > stats["newest_file"]:
                                stats["newest_file"] = stat.st_mtime
                                
                        except Exception as e:
                            log.warning(f"Error getting stats for {filepath}: {e}")
                            
        return stats