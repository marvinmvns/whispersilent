# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a real-time audio transcription system designed for Raspberry Pi 2W with Seeed VoiceCard. The system captures audio via ALSA, performs local transcription using Whisper.cpp, and sends results to an external API.

## Architecture

The system follows a modular pipeline architecture:

1. **AudioCapture** (`audioCapture.py`) - ALSA interface for audio capture
2. **AudioProcessor** (`audioProcessor.py`) - Speech detection and audio segmentation  
3. **WhisperService** (`whisperService.py`) - Local transcription via whisper.cpp executable
4. **ApiService** (`apiService.py`) - API client with retry logic
5. **TranscriptionPipeline** (`transcriptionPipeline.py`) - Main orchestrator
6. **Config** (`config.py`) - Centralized configuration management
7. **Logger** (`logger.py`) - Logging system

## Key Commands

### Setup and Installation
```bash
# Complete automated installation (recommended)
./install.sh

# Manual installation steps:
pip install -r requirements.txt
python3 setup.py
```

### Running the System
```bash
# Start with HTTP API server (recommended)
python3 mainWithServer.py

# Start basic transcription only
python3 main.py

# Using helper scripts
./start.sh      # Start the service
./test.sh       # Run tests
./status.sh     # Check service status
```

### Testing
```bash
# Run all tests
python -m pytest tests/

# Run specific test file
python -m pytest tests/test_audioCapture.py

# Run with verbose output
python -m pytest tests/ -v
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
- **CHUNK_DURATION_MS** - Audio chunk duration (default: 3000)
- **SILENCE_THRESHOLD** - Silence detection threshold (default: 500)
- **SILENCE_DURATION_MS** - Silence duration before processing (default: 1500)

## Important Implementation Details

### Audio Pipeline Flow
1. Continuous audio capture via ALSA
2. Real-time silence detection and voice activity detection
3. Audio segmentation into processable chunks
4. Local transcription using whisper.cpp subprocess
5. Asynchronous API delivery with retry logic

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
- **Installation Script** (`install.sh`) - Comprehensive automated installation with testing
- Dependency checking, virtual environment setup, and validation
- System service creation and helper scripts

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

## Whisper.cpp Integration

The system uses whisper.cpp as a subprocess with enhanced architecture detection and optimization. The setup script automatically detects system capabilities (CUDA, OpenCL, ARM NEON, x86 AVX) and compiles with appropriate flags for optimal performance.