# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a real-time audio transcription system designed for Raspberry Pi 2W with Seeed VoiceCard. The system captures audio via ALSA, performs local transcription using Whisper.cpp, and sends results to an external API.

## Architecture

The system follows a modular pipeline architecture:

1. **AudioCapture** (`src/core/audioCapture.py`) - ALSA interface for audio capture
2. **AudioProcessor** (`src/core/audioProcessor.py`) - Speech detection and audio segmentation  
3. **SpeechRecognitionService** (`src/transcription/speechRecognitionService.py`) - Comprehensive transcription with 12+ engines
4. **GoogleTranscribeService** (`src/transcription/googleTranscribeService.py`) - Legacy external transcription service
5. **ApiService** (`src/api/apiService.py`) - API client with retry logic
6. **TranscriptionPipeline** (`src/transcription/transcriptionPipeline.py`) - Main orchestrator
7. **Config** (`src/core/config.py`) - Centralized configuration management
8. **Logger** (`src/core/logger.py`) - Logging system
9. **HTTPServer** (`src/api/httpServer.py`) - REST API for monitoring and control
10. **HealthMonitor** (`src/services/healthMonitor.py`) - System health tracking
11. **AudioDeviceDetector** (`src/core/audioDeviceDetector.py`) - Automatic audio device detection and selection

## Key Commands

### Setup and Installation
```bash
# Complete automated installation (recommended)
./scripts/install_and_test.sh

# Choose installation type:
# 1. Full installation (system deps + Python deps + audio detection + tests)
# 2. Python dependencies only  
# 3. System dependencies only
# 4. Test existing installation

# Manual installation steps:
pip install -r requirements.txt
# Optional: Install specific speech recognition engines
pip install "SpeechRecognition[pocketsphinx]"  # CMU Sphinx (offline)
pip install "SpeechRecognition[vosk]"          # Vosk (offline) 
pip install "SpeechRecognition[whisper-local]" # Local Whisper (offline)
```

### Audio Device Detection and Configuration
```bash
# Automatic audio device detection (recommended)
python3 scripts/detect_audio_devices.py --auto

# Interactive device selection
python3 scripts/detect_audio_devices.py --interactive

# List all available audio devices
python3 scripts/detect_audio_devices.py --list

# Test specific device
python3 scripts/detect_audio_devices.py --test 2

# Auto-detect and update .env configuration
python3 scripts/detect_audio_devices.py --auto --update
```

### Running the System
```bash
# Start with HTTP API server (recommended)
python3 src/mainWithServer.py

# Start basic transcription only
python3 src/main.py

# Test the system
python3 tests/integration/test_full_system.py

# Run installation test
./scripts/install_and_test.sh
```

### Testing and Validation
```bash
# Run all pytest tests
python -m pytest tests/

# Run specific test file
python -m pytest tests/test_audioCapture.py

# Run with verbose output
python -m pytest tests/ -v

# === NEW COMPREHENSIVE TESTING SYSTEM ===

# Quick microphone validation (2 seconds)
python3 scripts/test_microphone_basic.py

# Complete transcription engine testing
python3 scripts/test_transcription_api.py

# Full system integration test (20+ seconds)
python3 scripts/test_complete_system.py

# Installation validation and health check
python3 scripts/validate_installation.py

# Original integration test
python3 tests/integration/test_full_system.py
```

### Audio Troubleshooting
```bash
# List audio capture devices
arecord -l

# Test audio capture (5 seconds)
arecord -D plughw:2,0 -f S16_LE -r 16000 -c 1 test.wav -d 5

# Play back test recording
aplay test.wav
```

## Configuration

The system uses environment variables loaded from `.env` file:

- **API_ENDPOINT** - Required: API endpoint for transcription results
- **API_KEY** - Required: API authentication key
- **WHISPER_MODEL_PATH** - Path to Whisper model (default: ./models/ggml-base.bin)
- **WHISPER_LANGUAGE** - Language code (default: pt)
- **SAMPLE_RATE** - Audio sample rate (default: 16000)
- **CHANNELS** - Audio channels (default: 1)
- **CHUNK_DURATION_MS** - Audio chunk duration (default: 3000)
- **SILENCE_THRESHOLD** - Silence detection threshold (default: 500)
- **SILENCE_DURATION_MS** - Silence duration before processing (default: 1500)
- **AUDIO_DEVICE** - Audio device configuration (default: auto)
  - `auto`: Automatic detection of best microphone (recommended)
  - `<number>`: Specific device index (e.g., 2)
  - `<name_part>`: Part of device name (e.g., "USB", "seeed")
  - `plughw:X,Y`: ALSA device specification (e.g., plughw:2,0)
- **SPEECH_RECOGNITION_ENGINE** - Speech recognition engine to use (default: google)
  - Available engines: google, google_cloud, sphinx, wit, azure, houndify, ibm, whisper_local, whisper_api, faster_whisper, groq, vosk, custom_endpoint
- **SPEECH_RECOGNITION_LANGUAGE** - Language code for speech recognition (default: pt-BR)
- **SPEECH_RECOGNITION_TIMEOUT** - Recognition timeout in seconds (default: 30)

### Engine-Specific Configuration
- **GOOGLE_CLOUD_CREDENTIALS_JSON** - Google Cloud credentials for google_cloud engine
- **WIT_AI_KEY** - Wit.ai API key for wit engine
- **AZURE_SPEECH_KEY** - Azure Speech API key for azure engine  
- **HOUNDIFY_CLIENT_ID** - Houndify client ID for houndify engine
- **OPENAI_API_KEY** - OpenAI API key for whisper_api engine
- **GROQ_API_KEY** - Groq API key for groq engine
- **VOSK_MODEL_PATH** - Path to Vosk model for vosk engine
- **CUSTOM_SPEECH_ENDPOINT** - Custom API endpoint for custom_endpoint engine

### Legacy Configuration (fallback)
- **GOOGLE_TRANSCRIBE_ENABLED** - Use legacy Google transcription service (default: false)
- **GOOGLE_TRANSCRIBE_ENDPOINT** - External transcription API endpoint
- **GOOGLE_TRANSCRIBE_KEY** - External transcription API key
- **GOOGLE_TRANSCRIBE_LANGUAGE** - Language code for external service (default: pt-BR)

## Important Implementation Details

### Audio Pipeline Flow
1. Continuous audio capture via ALSA
2. Real-time silence detection and voice activity detection
3. Audio segmentation into processable chunks
4. Transcription via configurable speech recognition engine:
   - **Google** (default): Free Google Speech Recognition API, requires internet
   - **Google Cloud**: Paid Google Cloud Speech API, high quality, requires credentials
   - **Sphinx**: Offline CMU Sphinx engine, moderate quality
   - **Vosk**: Offline Vosk engine, good quality, requires model download
   - **Whisper Local**: Offline OpenAI Whisper, best quality, high CPU usage
   - **Whisper API**: Online OpenAI Whisper API, excellent quality, requires API key
   - **Azure**: Microsoft Azure Speech API, requires API key
   - **IBM**: IBM Speech to Text API, requires credentials
   - **Wit.ai**: Facebook Wit.ai API, requires API key
   - **Houndify**: SoundHound Houndify API, requires credentials
   - **Groq**: Groq Whisper API, fast inference, requires API key
   - **Custom Endpoint**: User-defined API endpoint for transcription
5. Asynchronous API delivery with retry logic

### Speech Recognition Engine Selection
The system automatically selects the appropriate transcription engine based on the `SPEECH_RECOGNITION_ENGINE` environment variable. Feature toggles allow switching between:

- **Offline Engines**: sphinx, vosk, whisper_local, faster_whisper
- **Online Engines**: google, google_cloud, wit, azure, houndify, ibm, whisper_api, groq
- **Custom Integration**: custom_endpoint for proprietary APIs

### Engine Requirements
- **Free Online**: google (no API key required, rate limited)
- **Paid Online**: API keys/credentials required for all other online engines
- **Offline**: Model files required for sphinx, vosk, whisper_local engines
- **Hardware**: Offline engines may require significant CPU/memory resources

### Hardware Specifics
- Optimized for Raspberry Pi 2W (4 threads, no GPU)
- Uses Seeed VoiceCard (device: plughw:2,0)
- Audio format: 16kHz, 16-bit, mono WAV

### Error Handling
- Graceful signal handling (SIGINT, SIGTERM)
- Automatic retry on API failures
- Temporary file cleanup
- Comprehensive logging to logs/ directory

### Performance Considerations
- Asynchronous processing to avoid blocking audio capture
- Circular buffer for memory efficiency
- Automatic temporary file cleanup
- Queue-based processing for transcription order

## New Features Added

### Health Monitoring System
- **HealthMonitor** (`healthMonitor.py`) - Comprehensive system health tracking
- Real-time metrics: CPU, memory, processing times, error rates
- Performance warnings and degradation detection
- Component status monitoring

### HTTP API Server
- **HTTPServer** (`httpServer.py`) - RESTful API for monitoring and control
- **MainWithServer** (`mainWithServer.py`) - Main entry point with HTTP server
- Endpoints for health checks, transcription retrieval, and system control
- CORS support and JSON responses

### Transcription Storage & File Management
- **TranscriptionStorage** (`transcriptionStorage.py`) - In-memory transcription tracking
- **TranscriptionFiles** (`transcriptionFiles.py`) - Persistent file storage with chronological ordering
- Daily files, session exports, and readable transcripts
- Search, filtering, and statistics capabilities

### Enhanced Installation & Setup
- **Enhanced Setup** (`setup.py`) - Architecture detection and optimized compilation
- **Installation Script** (`install_and_test.sh`) - Comprehensive automated installation with testing
- Dependency checking, virtual environment setup, and validation
- System service creation and helper scripts

### Comprehensive Testing System
- **Basic Microphone Test** (`test_microphone_basic.py`) - Quick 2-second audio capture validation
- **Transcription API Test** (`test_transcription_api.py`) - Tests all available speech recognition engines
- **Complete System Test** (`test_complete_system.py`) - Full integration test with real-time audio processing
- **Installation Validator** (`validate_installation.py`) - Comprehensive system validation and health check
- Automatic integration with setup process for immediate validation
- Progressive testing from basic to advanced functionality

### API Control Features
- Toggle for proactive API sending (can disable automatic API calls)
- Manual transcription sending for unsent items
- Pipeline start/stop control via HTTP API
- Export functionality for transcription data

## HTTP API Endpoints

### Health & Monitoring
- `GET /health` - Basic health status
- `GET /health/detailed` - Comprehensive health information
- `GET /status` - Pipeline status and configuration

### Transcription Management
- `GET /transcriptions` - List transcriptions (with filters)
- `GET /transcriptions/search?q=text` - Search transcriptions
- `GET /transcriptions/statistics` - Get statistics
- `GET /transcriptions/{id}` - Get specific transcription
- `POST /transcriptions/export` - Export to JSON
- `POST /transcriptions/send-unsent` - Send pending transcriptions

### System Control
- `POST /control/toggle-api-sending` - Enable/disable automatic API sending
- `POST /control/start` - Start pipeline
- `POST /control/stop` - Stop pipeline

## Testing and Validation Workflow

### Installation Testing Process
1. **Automated Setup Tests** - Run during `./scripts/install_and_test.sh`
   - Module import validation
   - Configuration loading verification
   - Basic microphone functionality test
   - Transcription engine availability check

2. **Manual Testing Options**
   - **Quick Validation**: `python scripts/test_microphone_basic.py` (2s test)
   - **Engine Testing**: `python scripts/test_transcription_api.py` (comprehensive engine validation)
   - **Full System Test**: `python scripts/test_complete_system.py` (20+ second real-time test)
   - **Health Check**: `python scripts/validate_installation.py` (installation verification)

### Test Coverage
- **Audio Capture**: Device detection, initialization, real-time capture with signal analysis
- **Speech Recognition**: All 12+ engines tested with mock and real audio data
- **API Integration**: Connection testing, data sending validation, response time measurement
- **System Integration**: End-to-end workflow from audio capture to API delivery
- **Error Handling**: Network failures, device issues, engine switching, timeout scenarios

### Test Output and Reporting
- Real-time progress indicators with emoji status
- Detailed performance metrics (processing times, success rates, amplitude analysis)
- Comprehensive error reporting with suggested solutions
- Final validation reports with component status and next steps
- Integration with setup process for immediate feedback

## Whisper.cpp Integration

The system uses whisper.cpp as a subprocess with enhanced architecture detection and optimization. The setup script automatically detects system capabilities (CUDA, OpenCL, ARM NEON, x86 AVX) and compiles with appropriate flags for optimal performance.