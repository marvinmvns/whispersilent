#!/usr/bin/env python3
"""
Test script that captures audio from all available microphones and transcribes using Google's free API
"""

import sys
import os
import time
import numpy as np
import sounddevice as sd
import speech_recognition as sr
from typing import List, Dict, Optional, Tuple
import threading
import queue

# Add src directories to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src', 'core'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src', 'transcription'))

from audioDeviceDetector import AudioDeviceDetector
from logger import log

class MicrophoneTranscriptionTester:
    """Test class for microphone transcription with Google API"""
    
    def __init__(self):
        self.device_detector = AudioDeviceDetector()
        self.recognizer = sr.Recognizer()
        self.recording_duration = 5.0  # seconds
        self.sample_rate = 16000
        self.channels = 1
        
    def test_all_microphones(self):
        """Test transcription with all available microphones"""
        print("\n🎤 Teste de Transcrição com Microfones Disponíveis")
        print("=" * 60)
        print("🔊 Usando Google Speech Recognition (gratuito, sem API key)")
        print("⏱️ Duração da gravação: 5 segundos por dispositivo")
        print("🗣️ Fale algo durante a gravação para testar a transcrição")
        print("=" * 60)
        
        input_devices = self.device_detector.get_input_devices()
        
        if not input_devices:
            print("❌ Nenhum dispositivo de entrada encontrado!")
            return
        
        print(f"\n📱 Encontrados {len(input_devices)} dispositivos de entrada:")
        
        successful_tests = []
        failed_tests = []
        
        for i, device in enumerate(input_devices):
            device_index = device['index']
            device_info = device['info']
            device_name = device_info['name']
            
            print(f"\n--- Teste {i+1}/{len(input_devices)} ---")
            print(f"🎯 Dispositivo: {device_name}")
            print(f"📊 Índice: {device_index}")
            print(f"🔢 Canais de entrada: {device_info['max_input_channels']}")
            print(f"📈 Taxa de amostra: {device_info['default_samplerate']} Hz")
            
            # Check if device looks like a microphone
            is_mic = self.device_detector.is_microphone_device(device_info)
            mic_indicator = "📱" if is_mic else "🔊"
            print(f"🎤 Tipo: {mic_indicator} {'Provável microfone' if is_mic else 'Dispositivo genérico'}")
            
            # Test the device
            try:
                print(f"\n⏳ Testando captura de áudio... (gravando por {self.recording_duration}s)")
                print("🗣️ FALE AGORA!")
                
                # Record audio
                audio_data = self._record_audio(device_index)
                
                if audio_data is None:
                    failed_tests.append((device_index, device_name, "Falha na captura de áudio"))
                    print("❌ Falha na captura de áudio")
                    continue
                
                # Analyze audio signal
                signal_stats = self._analyze_audio_signal(audio_data)
                print(f"📊 Estatísticas do sinal:")
                print(f"   - Amplitude máxima: {signal_stats['max_amplitude']:.2f}")
                print(f"   - Amplitude RMS: {signal_stats['rms']:.2f}")
                print(f"   - Variância: {signal_stats['variance']:.2f}")
                print(f"   - Energia do sinal: {signal_stats['energy']:.2f}")
                
                if signal_stats['max_amplitude'] < 100:
                    print("⚠️ Sinal muito baixo - pode ser apenas ruído")
                
                # Transcribe using Google
                print("🔄 Transcrevendo com Google Speech Recognition...")
                transcription = self._transcribe_with_google(audio_data)
                
                if transcription:
                    print(f"✅ Transcrição: \"{transcription}\"")
                    successful_tests.append((device_index, device_name, transcription, signal_stats))
                else:
                    print("🔇 Nenhuma fala detectada ou transcrição vazia")
                    failed_tests.append((device_index, device_name, "Transcrição vazia"))
                
            except Exception as e:
                error_msg = str(e)
                print(f"❌ Erro durante o teste: {error_msg}")
                failed_tests.append((device_index, device_name, error_msg))
            
            print("-" * 40)
            
            # Small pause between tests
            if i < len(input_devices) - 1:
                time.sleep(1)
        
        # Summary
        self._print_summary(successful_tests, failed_tests)
    
    def _record_audio(self, device_index: int) -> Optional[np.ndarray]:
        """Record audio from specific device"""
        try:
            # Record audio
            recording = sd.rec(
                int(self.recording_duration * self.sample_rate),
                samplerate=self.sample_rate,
                channels=self.channels,
                device=device_index,
                dtype='int16'
            )
            sd.wait()  # Wait for recording to complete
            
            return recording.flatten()  # Convert to 1D array
            
        except Exception as e:
            log.error(f"Error recording from device {device_index}: {e}")
            return None
    
    def _analyze_audio_signal(self, audio_data: np.ndarray) -> Dict:
        """Analyze audio signal properties"""
        stats = {
            'max_amplitude': float(np.max(np.abs(audio_data))),
            'rms': float(np.sqrt(np.mean(audio_data.astype(np.float64) ** 2))),
            'variance': float(np.var(audio_data.astype(np.float64))),
            'energy': float(np.sum(audio_data.astype(np.float64) ** 2))
        }
        return stats
    
    def _transcribe_with_google(self, audio_data: np.ndarray) -> str:
        """Transcribe audio using Google Speech Recognition (free)"""
        try:
            # Convert numpy array to AudioData format
            import io
            import wave
            
            # Create WAV bytes in memory
            byte_io = io.BytesIO()
            with wave.open(byte_io, 'wb') as wav_file:
                wav_file.setnchannels(self.channels)
                wav_file.setsampwidth(2)  # 16-bit
                wav_file.setframerate(self.sample_rate)
                wav_file.writeframes(audio_data.tobytes())
            
            # Create AudioData object
            byte_io.seek(0)
            audio_sr = sr.AudioData(
                byte_io.getvalue(),
                self.sample_rate,
                2  # 16-bit = 2 bytes
            )
            
            # Perform recognition with Google (free)
            try:
                transcription = self.recognizer.recognize_google(
                    audio_sr,
                    language='pt-BR'  # Portuguese (Brazil)
                )
                return transcription.strip() if transcription else ""
                
            except sr.UnknownValueError:
                # No speech detected
                return ""
            except sr.RequestError as e:
                log.error(f"Google Speech Recognition API error: {e}")
                return ""
                
        except Exception as e:
            log.error(f"Error in transcription: {e}")
            return ""
    
    def _print_summary(self, successful_tests: List, failed_tests: List):
        """Print test summary"""
        print("\n" + "=" * 60)
        print("📋 RESUMO DOS TESTES")
        print("=" * 60)
        
        total_tests = len(successful_tests) + len(failed_tests)
        print(f"📊 Total de dispositivos testados: {total_tests}")
        print(f"✅ Testes bem-sucedidos: {len(successful_tests)}")
        print(f"❌ Testes falharam: {len(failed_tests)}")
        
        if successful_tests:
            print(f"\n🎉 DISPOSITIVOS COM TRANSCRIÇÃO BEM-SUCEDIDA:")
            for device_index, device_name, transcription, stats in successful_tests:
                print(f"   📱 [{device_index}] {device_name}")
                print(f"      💬 Transcrição: \"{transcription}\"")
                print(f"      📊 Amplitude máxima: {stats['max_amplitude']:.2f}")
                print(f"      🔊 RMS: {stats['rms']:.2f}")
                print()
        
        if failed_tests:
            print(f"\n⚠️ DISPOSITIVOS COM FALHAS:")
            for device_index, device_name, error in failed_tests:
                print(f"   🔴 [{device_index}] {device_name}")
                print(f"      ❌ Erro: {error}")
                print()
        
        if successful_tests:
            print("💡 RECOMENDAÇÕES:")
            # Find device with best signal quality
            best_device = max(successful_tests, key=lambda x: x[3]['rms'])
            device_index, device_name, transcription, stats = best_device
            print(f"   🏆 Melhor dispositivo: [{device_index}] {device_name}")
            print(f"   📝 Para usar este dispositivo, configure AUDIO_DEVICE={device_index} no .env")
            print()
            
        print("🔧 PRÓXIMOS PASSOS:")
        print("   1. Use o melhor dispositivo identificado no seu .env")
        print("   2. Execute o sistema principal: python3 src/mainWithServer.py")
        print("   3. Teste a transcrição em tempo real")
        print("=" * 60)

def main():
    """Main function"""
    try:
        print("🚀 Iniciando teste de transcrição com microfones...")
        
        # Check if speech_recognition is available
        try:
            import speech_recognition as sr
            print("✅ SpeechRecognition library disponível")
        except ImportError:
            print("❌ SpeechRecognition library não encontrada!")
            print("💡 Instale com: pip install SpeechRecognition")
            return
        
        # Check if sounddevice is available
        try:
            import sounddevice as sd
            print("✅ SoundDevice library disponível")
        except ImportError:
            print("❌ SoundDevice library não encontrada!")
            print("💡 Instale com: pip install sounddevice")
            return
        
        # Create and run tester
        tester = MicrophoneTranscriptionTester()
        tester.test_all_microphones()
        
    except KeyboardInterrupt:
        print("\n\n⏹️ Teste cancelado pelo usuário")
    except Exception as e:
        print(f"\n❌ Erro durante o teste: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()