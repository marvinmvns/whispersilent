#!/usr/bin/env python3
"""
Vosk Microphone Calibration Tool
Captures and analyzes microphone data to help calibrate Vosk transcription settings.
"""

import sys
import os
import numpy as np
import pyaudio
import time
import json
import wave
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src', 'core'))
from config import Config
from logger import log

class VoskMicrophoneCalibrator:
    def __init__(self):
        self.sample_rate = Config.AUDIO.get("sample_rate", 16000)
        self.channels = Config.AUDIO.get("channels", 1)
        self.chunk_duration_ms = Config.AUDIO.get("chunk_duration_ms", 3000)
        self.silence_threshold = Config.AUDIO.get("silence_threshold", 500)
        
        # Calculate chunk size in samples
        self.chunk_size = int(self.sample_rate * self.chunk_duration_ms / 1000)
        
        self.audio = pyaudio.PyAudio()
        self.device_index = self._get_audio_device()
        
        print(f"🎙️  Vosk Microphone Calibrator")
        print(f"📊 Sample Rate: {self.sample_rate}Hz")
        print(f"📻 Channels: {self.channels}")
        print(f"⏱️  Chunk Duration: {self.chunk_duration_ms}ms")
        print(f"🎚️  Current Silence Threshold: {self.silence_threshold}")
        print(f"🎧 Audio Device: {self.device_index}")
        print()

    def _get_audio_device(self):
        """Get audio device index from config"""
        audio_device = Config.AUDIO.get("device", "auto")
        
        if audio_device == "auto":
            # Find default input device
            device_info = self.audio.get_default_input_device_info()
            return int(device_info["index"])
        elif isinstance(audio_device, int) or audio_device.isdigit():
            return int(audio_device)
        else:
            # Search by name
            device_count = self.audio.get_device_count()
            for i in range(device_count):
                device_info = self.audio.get_device_info_by_index(i)
                if audio_device.lower() in device_info["name"].lower():
                    return i
            
            # Fallback to default
            device_info = self.audio.get_default_input_device_info()
            return int(device_info["index"])

    def analyze_audio_levels(self, duration_seconds=10):
        """Analyze microphone audio levels for calibration"""
        print(f"🔊 Analyzing audio levels for {duration_seconds} seconds...")
        print("📢 Please speak normally during this time!")
        print()
        
        # Audio stream setup
        stream = self.audio.open(
            format=pyaudio.paInt16,
            channels=self.channels,
            rate=self.sample_rate,
            input=True,
            input_device_index=self.device_index,
            frames_per_buffer=1024
        )
        
        audio_data = []
        amplitudes = []
        start_time = time.time()
        
        try:
            while time.time() - start_time < duration_seconds:
                # Read audio chunk
                data = stream.read(1024, exception_on_overflow=False)
                audio_chunk = np.frombuffer(data, dtype=np.int16)
                
                # Calculate amplitude
                amplitude = np.abs(audio_chunk).mean()
                amplitudes.append(amplitude)
                audio_data.extend(audio_chunk)
                
                # Real-time feedback
                elapsed = time.time() - start_time
                remaining = duration_seconds - elapsed
                
                # Simple level meter
                level_bars = int(amplitude / 100)
                level_display = "█" * min(level_bars, 20)
                
                print(f"\r⏱️  {remaining:.1f}s | 📊 {amplitude:5.0f} | {level_display:<20}", end="", flush=True)
                
                time.sleep(0.1)
                
        finally:
            stream.stop_stream()
            stream.close()
            print("\n")
        
        return np.array(audio_data), np.array(amplitudes)

    def calculate_calibration_values(self, amplitudes):
        """Calculate recommended calibration values from amplitude data"""
        if len(amplitudes) == 0:
            return None
            
        stats = {
            "mean": np.mean(amplitudes),
            "median": np.median(amplitudes),
            "std": np.std(amplitudes),
            "min": np.min(amplitudes),
            "max": np.max(amplitudes),
            "q25": np.percentile(amplitudes, 25),
            "q75": np.percentile(amplitudes, 75),
            "q90": np.percentile(amplitudes, 90),
            "q95": np.percentile(amplitudes, 95)
        }
        
        # Calculate recommended thresholds
        # Silence threshold should be above background noise but below speech
        background_noise = stats["q25"]  # 25th percentile as background
        speech_level = stats["q75"]      # 75th percentile as typical speech
        
        recommended_silence_threshold = max(
            int(background_noise * 1.5),  # 50% above background noise
            int(speech_level * 0.3),      # 30% of speech level
            100  # Minimum threshold
        )
        
        return {
            "statistics": stats,
            "current_silence_threshold": self.silence_threshold,
            "recommended_silence_threshold": recommended_silence_threshold,
            "background_noise_level": int(background_noise),
            "speech_level": int(speech_level),
            "signal_to_noise_ratio": speech_level / max(background_noise, 1)
        }

    def save_calibration_sample(self, audio_data, filename=None):
        """Save audio sample for further analysis"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"vosk_calibration_sample_{timestamp}.wav"
        
        filepath = os.path.join(os.path.dirname(__file__), "..", "logs", filename)
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        with wave.open(filepath, 'wb') as wav_file:
            wav_file.setnchannels(self.channels)
            wav_file.setsampwidth(2)  # 16-bit
            wav_file.setframerate(self.sample_rate)
            wav_file.writeframes(audio_data.astype(np.int16).tobytes())
        
        return filepath

    def print_calibration_report(self, calibration_data):
        """Print detailed calibration report"""
        stats = calibration_data["statistics"]
        
        print("🎯 VOSK MICROPHONE CALIBRATION REPORT")
        print("=" * 50)
        print()
        
        print("📈 AUDIO LEVEL STATISTICS:")
        print(f"  📊 Mean Level:      {stats['mean']:6.0f}")
        print(f"  📊 Median Level:    {stats['median']:6.0f}")
        print(f"  📊 Min Level:       {stats['min']:6.0f}")
        print(f"  📊 Max Level:       {stats['max']:6.0f}")
        print(f"  📊 25th Percentile: {stats['q25']:6.0f}")
        print(f"  📊 75th Percentile: {stats['q75']:6.0f}")
        print(f"  📊 95th Percentile: {stats['q95']:6.0f}")
        print()
        
        print("🎚️  THRESHOLD ANALYSIS:")
        print(f"  🔇 Background Noise Level:    {calibration_data['background_noise_level']:6.0f}")
        print(f"  🗣️  Typical Speech Level:     {calibration_data['speech_level']:6.0f}")
        print(f"  📶 Signal-to-Noise Ratio:    {calibration_data['signal_to_noise_ratio']:6.1f}")
        print()
        
        print("⚙️  CONFIGURATION RECOMMENDATIONS:")
        print(f"  🎚️  Current Silence Threshold:     {calibration_data['current_silence_threshold']}")
        print(f"  ✅ Recommended Silence Threshold: {calibration_data['recommended_silence_threshold']}")
        print()
        
        # Quality assessment
        snr = calibration_data['signal_to_noise_ratio']
        if snr > 5:
            quality = "🟢 EXCELLENT"
        elif snr > 3:
            quality = "🟡 GOOD"
        elif snr > 2:
            quality = "🟠 FAIR"
        else:
            quality = "🔴 POOR"
            
        print(f"🎤 MICROPHONE QUALITY: {quality}")
        print()
        
        if calibration_data['recommended_silence_threshold'] != calibration_data['current_silence_threshold']:
            print("💡 SUGGESTED .env UPDATE:")
            print(f"   SILENCE_THRESHOLD={calibration_data['recommended_silence_threshold']}")
            print()

    def run_calibration(self, duration=10, save_sample=True):
        """Run complete calibration process"""
        print("🎯 Starting Vosk Microphone Calibration")
        print("=" * 50)
        print()
        
        try:
            # Analyze audio levels
            audio_data, amplitudes = self.analyze_audio_levels(duration)
            
            # Calculate calibration values
            calibration_data = self.calculate_calibration_values(amplitudes)
            
            if calibration_data is None:
                print("❌ No audio data captured. Please check your microphone.")
                return None
            
            # Save audio sample
            sample_path = None
            if save_sample:
                sample_path = self.save_calibration_sample(audio_data)
                print(f"💾 Audio sample saved: {sample_path}")
                print()
            
            # Print report
            self.print_calibration_report(calibration_data)
            
            # Save calibration report
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_path = os.path.join(os.path.dirname(__file__), "..", "logs", f"vosk_calibration_{timestamp}.json")
            os.makedirs(os.path.dirname(report_path), exist_ok=True)
            
            calibration_data["timestamp"] = timestamp
            calibration_data["sample_path"] = sample_path
            calibration_data["config"] = {
                "sample_rate": self.sample_rate,
                "channels": self.channels,
                "chunk_duration_ms": self.chunk_duration_ms,
                "device_index": self.device_index
            }
            
            with open(report_path, 'w') as f:
                json.dump(calibration_data, f, indent=2, default=str)
            
            print(f"📄 Calibration report saved: {report_path}")
            
            return calibration_data
            
        except Exception as e:
            print(f"❌ Calibration failed: {e}")
            return None
        
        finally:
            self.audio.terminate()

def main():
    """Main calibration function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Vosk Microphone Calibration Tool")
    parser.add_argument("--duration", type=int, default=10, help="Calibration duration in seconds (default: 10)")
    parser.add_argument("--no-save", action="store_true", help="Don't save audio sample")
    
    args = parser.parse_args()
    
    calibrator = VoskMicrophoneCalibrator()
    result = calibrator.run_calibration(
        duration=args.duration,
        save_sample=not args.no_save
    )
    
    if result:
        print("✅ Calibration completed successfully!")
        return 0
    else:
        print("❌ Calibration failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())