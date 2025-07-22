# 🎤 WhisperSilent - Advanced Real-time Transcription System

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Platform](https://img.shields.io/badge/platform-linux%20%7C%20macos%20%7C%20raspberry--pi-lightgrey.svg)](https://github.com/whispersilent)

**🚀 Professional-grade real-time transcription system with advanced features**

Comprehensive audio transcription platform featuring **speaker identification**, **real-time WebSocket streaming**, **hourly aggregation**, and a complete **REST API**. Optimized for Raspberry Pi and embedded devices.

## ✨ Key Features

### 🎯 Core Transcription
- 🎤 **Real-time audio capture** using ALSA/PortAudio
- 🧠 **12+ speech recognition engines** (Google, Whisper, Vosk, Azure, etc.)
- 🔄 **Online & Offline** processing capabilities  
- 📊 **Quality control** with confidence scoring

### 🎭 Speaker Identification (Feature Toggle)
- 👥 **Multi-speaker detection** and tracking
- 🧠 **4 identification methods**: Simple Energy, PyAnnote, Resemblyzer, SpeechBrain
- 📈 **Speaker profiles** with confidence scoring
- 🔧 **Configurable thresholds** and parameters

### 📡 Real-time WebSocket API
- ⚡ **Live transcription streaming** to multiple clients
- 🔔 **Event subscriptions**: transcriptions, speaker changes, system status
- 🌐 **Multi-client support** (up to 50 concurrent connections)
- 📱 **Web and Python clients** included

### ⏰ Intelligent Aggregation  
- 📋 **Hourly text aggregation** to reduce API load
- 🔇 **Silence gap detection** (5+ minutes triggers finalization)
- 📊 **Rich metadata** tracking (word counts, processing times)
- 🔍 **Partial queries** during aggregation

### 🌐 Complete REST API
- 🏥 **Health monitoring** with CPU/memory metrics
- 📝 **Transcription management** and search
- 🎛️ **System control** (start/stop, configuration)
- 📖 **Interactive Swagger documentation**

### 🔧 Professional Features
- 📈 **Performance monitoring** and analytics
- 💾 **Persistent storage** with chronological organization
- 🔄 **Automatic retry logic** for API calls
- 🚀 **Raspberry Pi optimized** with architecture detection

## 📋 System Requirements

### Hardware
- **CPU**: Raspberry Pi 2W+ or x86_64 (ARM64, ARMv7 supported)
- **Memory**: 1GB RAM minimum, 2GB+ recommended
- **Storage**: 5GB available space
- **Audio**: USB microphone or Seeed VoiceCard

### Software
- **OS**: Linux (Ubuntu/Debian), macOS, Windows
- **Python**: 3.8+ with pip and venv
- **Internet**: Optional (for online engines and model downloads)

## ⚡ Quick Installation

### Automated Setup (Recommended)

```bash
# Clone repository
git clone https://github.com/your-username/whispersilent.git
cd whispersilent

# Run complete installation with testing
chmod +x scripts/install_and_test.sh
./scripts/install_and_test.sh
```

The installation script will:
- ✅ Install system dependencies
- ✅ Set up Python virtual environment
- ✅ Download and compile optimized binaries
- ✅ Download transcription models
- ✅ Run comprehensive validation tests
- ✅ Configure audio devices automatically

### Manual Installation

```bash
# 1. System dependencies (Ubuntu/Debian)
sudo apt update && sudo apt install -y \\
    python3 python3-pip python3-venv \\
    build-essential cmake git wget \\
    portaudio19-dev alsa-utils

# 2. Python environment
python3 -m venv venv
source venv/bin/activate

# 3. Python dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
nano .env

# 5. Download models and test
python3 scripts/validate_installation.py
```

## 🔧 Configuration

### Basic Configuration (.env)

```bash
# === CORE AUDIO SETTINGS ===
AUDIO_DEVICE=auto                    # Auto-detect best microphone
SAMPLE_RATE=16000
CHANNELS=1

# === SPEECH RECOGNITION ===
SPEECH_RECOGNITION_ENGINE=google     # Free Google API (default)
SPEECH_RECOGNITION_LANGUAGE=pt-BR
SPEECH_RECOGNITION_TIMEOUT=30

# === API INTEGRATION (OPTIONAL) ===
API_ENDPOINT=https://your-api.com/transcribe
API_KEY=your_api_key

# === HTTP SERVER ===
HTTP_HOST=localhost
HTTP_PORT=8080

# === FEATURE TOGGLES ===
SPEAKER_IDENTIFICATION_ENABLED=false
REALTIME_API_ENABLED=false
LOG_LEVEL=INFO
```

### Advanced Features

#### Speaker Identification

```bash
# Enable speaker identification
SPEAKER_IDENTIFICATION_ENABLED=true
SPEAKER_IDENTIFICATION_METHOD=simple_energy

# Available methods:
# - simple_energy: Basic energy-based (no dependencies)
# - pyannote: Neural speaker diarization (requires model)
# - resemblyzer: Speaker embeddings (pip install resemblyzer)
# - speechbrain: Advanced recognition (pip install speechbrain)

# Fine-tuning
SPEAKER_CONFIDENCE_THRESHOLD=0.7
SPEAKER_MIN_SEGMENT_DURATION=2.0
SPEAKER_MAX_SPEAKERS=10
```

#### Real-time WebSocket API

```bash
# Enable real-time streaming
REALTIME_API_ENABLED=true
REALTIME_WEBSOCKET_PORT=8081
REALTIME_MAX_CONNECTIONS=50
REALTIME_BUFFER_SIZE=100
```

#### Speech Recognition Engines

**Online Engines** (require internet):
```bash
# Google (free, default)
SPEECH_RECOGNITION_ENGINE=google

# OpenAI Whisper API (excellent quality)
SPEECH_RECOGNITION_ENGINE=whisper_api
OPENAI_API_KEY=your_openai_key

# Google Cloud (high quality)
SPEECH_RECOGNITION_ENGINE=google_cloud
GOOGLE_CLOUD_CREDENTIALS_JSON=path/to/credentials.json

# Azure, IBM, Wit.ai, Houndify, Groq
SPEECH_RECOGNITION_ENGINE=azure
AZURE_SPEECH_KEY=your_azure_key
```

**Offline Engines** (work without internet):
```bash
# Vosk (good quality, requires model download)
SPEECH_RECOGNITION_ENGINE=vosk
VOSK_MODEL_PATH=path/to/vosk-model

# Local Whisper (best quality, high CPU)
SPEECH_RECOGNITION_ENGINE=whisper_local
WHISPER_MODEL=base

# CMU Sphinx (lightweight)
SPEECH_RECOGNITION_ENGINE=sphinx
```

## 🚀 Usage

### Start the System

```bash
# Complete system with HTTP server and real-time API
python3 src/mainWithServer.py

# Basic transcription only
python3 src/main.py
```

### Access Interfaces

- **🏥 Health Dashboard**: http://localhost:8080/health
- **📖 API Documentation**: http://localhost:8080/api-docs  
- **📝 Transcriptions**: http://localhost:8080/transcriptions
- **📡 Real-time Client**: Open `examples/realtime_web_client.html`
- **🔌 WebSocket**: `ws://localhost:8081`

### Testing & Validation

```bash
# Quick microphone test (2 seconds)
python3 scripts/test_microphone_basic.py

# Test all available speech engines
python3 scripts/test_transcription_api.py

# Complete system integration test (20+ seconds)
python3 scripts/test_complete_system.py

# Full installation validation
python3 scripts/validate_installation.py

# Audio device detection and configuration
python3 scripts/detect_audio_devices.py --auto --update
```

## 🌐 API Reference

### REST API Endpoints

#### Health & Monitoring
```bash
GET /health                    # Basic health status
GET /health/detailed          # Comprehensive system metrics
GET /status                   # Pipeline status and configuration
```

#### Transcription Management
```bash
GET /transcriptions                              # List all transcriptions
GET /transcriptions?limit=50                     # Last 50 transcriptions
GET /transcriptions?recent_minutes=60            # Last hour
GET /transcriptions/search?q=keyword             # Search transcriptions
GET /transcriptions/statistics                   # Get statistics
GET /transcriptions/{id}                         # Specific transcription
POST /transcriptions/export                      # Export to JSON
POST /transcriptions/send-unsent                 # Send pending to API
```

#### Hourly Aggregation
```bash
GET /aggregation/status                          # Current aggregation status
GET /aggregation/texts                           # List aggregated texts
GET /aggregation/texts/{hour_timestamp}          # Specific hour
POST /aggregation/finalize                       # Force finalization
POST /aggregation/toggle?enabled=true           # Enable/disable
GET /aggregation/statistics                      # Aggregation stats
```

#### Speaker Identification
```bash
GET /speakers/profiles                           # All speaker profiles
GET /speakers/statistics                         # Speaker identification stats
PUT /speakers/{id}/name                          # Update speaker name
DELETE /speakers/{id}                            # Remove speaker profile
POST /speakers/toggle?enabled=true               # Enable/disable feature
```

#### System Control
```bash
POST /control/start                              # Start transcription pipeline
POST /control/stop                               # Stop transcription pipeline
POST /control/toggle-api-sending                 # Toggle external API calls
```

#### Real-time API
```bash
GET /realtime/status                             # WebSocket server status
GET /realtime/statistics                         # Real-time API statistics
```

### WebSocket API

#### Connection
```javascript
const ws = new WebSocket('ws://localhost:8081');

ws.onmessage = function(event) {
    const data = JSON.parse(event.data);
    console.log('Event:', data);
};
```

#### Event Types
- **transcription**: New transcription text
- **speaker_change**: Speaker identification update  
- **chunk_processed**: Audio processing status
- **heartbeat**: Server status and metrics
- **error**: System errors and warnings

#### Client Commands
```javascript
// Subscribe to events
ws.send(JSON.stringify({
    action: 'subscribe',
    events: ['transcription', 'speaker_change']
}));

// Send heartbeat
ws.send(JSON.stringify({
    action: 'ping',
    timestamp: Date.now() / 1000
}));

// Request recent events
ws.send(JSON.stringify({
    action: 'get_buffer'
}));
```

## 🏗️ System Architecture

```
┌─────────────┐    ┌──────────────┐    ┌─────────────────┐
│ Microphone  │───▶│ AudioCapture │───▶│ AudioProcessor  │
│ (USB/ALSA)  │    │   (Thread)   │    │ (VAD/Chunking)  │
└─────────────┘    └──────────────┘    └─────────────────┘
                                                  │
                                                  ▼
┌─────────────┐    ┌──────────────┐    ┌─────────────────┐
│Speaker ID   │◀───│ Transcription│◀───│ SpeechRecognition│
│Service      │    │ Pipeline     │    │ Service (12+)   │
└─────────────┘    └──────────────┘    └─────────────────┘
                            │                     │
                            ▼                     ▼
┌─────────────┐    ┌──────────────┐    ┌─────────────────┐
│Hourly       │    │Health        │    │ Storage &       │
│Aggregator   │    │Monitor       │    │ File Management │
└─────────────┘    └──────────────┘    └─────────────────┘
                            │
                            ▼
┌─────────────┐    ┌──────────────┐    ┌─────────────────┐
│Real-time    │    │HTTP Server   │    │ External API    │
│WebSocket API│    │(REST API)    │    │ (Optional)      │
└─────────────┘    └──────────────┘    └─────────────────┘
```

### Core Components

1. **AudioCapture**: ALSA/PortAudio interface with automatic device detection
2. **AudioProcessor**: Voice activity detection and intelligent segmentation
3. **SpeechRecognitionService**: Unified interface for 12+ recognition engines
4. **SpeakerIdentificationService**: Multi-method speaker identification (feature toggle)
5. **HourlyAggregator**: Intelligent text aggregation with silence detection
6. **RealtimeAPI**: WebSocket server for live transcription streaming
7. **TranscriptionPipeline**: Main orchestrator with health monitoring
8. **HTTPServer**: Complete REST API with Swagger documentation
9. **HealthMonitor**: System performance and resource monitoring

## 📊 Performance & Monitoring

### Health Metrics

```json
{
  "status": "healthy",
  "timestamp": 1704067200.0,
  "uptime_seconds": 3600,
  "summary": {
    "pipeline_running": true,
    "total_transcriptions": 150,
    "cpu_usage": 25.5,
    "memory_usage": 65.2,
    "recent_errors_count": 0,
    "api_success_rate": 98.5
  },
  "system_metrics": {
    "cpu_percent": 25.5,
    "memory_percent": 65.2,
    "process_memory_mb": 245.7,
    "process_threads": 8,
    "disk_usage_percent": 42.1
  }
}
```

### Performance Benchmarks (Raspberry Pi 4)

| Model | Size | Latency | CPU Usage | Memory |
|-------|------|---------|-----------|---------|
| tiny | 39 MB | 0.5-1s | 30% | 150MB |
| base | 142 MB | 1-2s | 50% | 250MB |
| small | 466 MB | 2-4s | 70% | 400MB |

### Real-time Analytics

- 📈 **Processing Times**: Average transcription latency
- 🎯 **Success Rates**: Transcription and API call success
- 💾 **Resource Usage**: CPU, memory, disk monitoring
- 👥 **Speaker Analytics**: Speaker identification accuracy
- 🌐 **Connection Health**: WebSocket client monitoring

## 📁 Project Structure

```
whispersilent/
├── 📁 src/                          # Source code
│   ├── 🐍 main.py                   # Basic entry point
│   ├── 🌐 mainWithServer.py         # Full system entry point
│   ├── 📁 core/                     # Core components
│   │   ├── config.py               # Centralized configuration
│   │   ├── logger.py               # Logging system
│   │   ├── audioCapture.py         # Audio capture interface
│   │   ├── audioProcessor.py       # Audio processing
│   │   └── audioDeviceDetector.py  # Device auto-detection
│   ├── 📁 transcription/            # Transcription services
│   │   ├── speechRecognitionService.py     # 12+ engines
│   │   ├── transcriptionPipeline.py        # Main orchestrator
│   │   ├── transcriptionStorage.py         # In-memory storage
│   │   └── transcriptionFiles.py           # File management
│   ├── 📁 api/                      # API services
│   │   ├── httpServer.py           # REST API server
│   │   ├── realtimeAPI.py          # WebSocket server
│   │   ├── apiService.py           # External API client
│   │   └── swagger.py              # API documentation
│   └── 📁 services/                 # Advanced services
│       ├── healthMonitor.py        # System monitoring
│       ├── hourlyAggregator.py     # Text aggregation
│       └── speakerIdentification.py # Speaker features
├── 📁 scripts/                      # Automation & testing
│   ├── 🔧 install_and_test.sh      # Complete installation
│   ├── 🧪 test_complete_system.py  # Integration testing
│   ├── 🎤 test_microphone_basic.py # Quick audio test
│   ├── 📡 test_transcription_api.py # Engine testing
│   └── 🔍 validate_installation.py # Installation validator
├── 📁 examples/                     # Client examples
│   ├── 🐍 realtime_client.py       # Python WebSocket client
│   └── 🌐 realtime_web_client.html # Web interface
├── 📁 docs/                         # Documentation
│   ├── 📁 api/                      # API documentation
│   ├── 📁 installation/             # Setup guides
│   ├── 📁 features/                 # Feature documentation
│   └── 📁 examples/                 # Usage examples
├── 📁 models/                       # AI models (downloaded)
├── 📁 transcriptions/               # Output data
├── 📁 tests/                        # Test suite
├── 🔧 requirements.txt              # Python dependencies
├── ⚙️ .env.example                  # Configuration template
├── 📋 .gitignore                    # Git ignore rules
└── 📖 README.md                     # This file
```

## 🔧 Advanced Configuration

### Raspberry Pi Optimization

```bash
# Lightweight model for Pi 2W
WHISPER_MODEL_PATH=./models/ggml-tiny.bin

# Reduced chunk size for lower latency
CHUNK_DURATION_MS=2000

# Optimized thread count
WHISPER_THREADS=2

# Energy-based speaker detection (no AI dependencies)
SPEAKER_IDENTIFICATION_METHOD=simple_energy
```

### High-Quality Setup

```bash
# Best quality model
WHISPER_MODEL_PATH=./models/ggml-large-v3.bin

# OpenAI Whisper API for cloud processing
SPEECH_RECOGNITION_ENGINE=whisper_api
OPENAI_API_KEY=your_openai_key

# Advanced speaker identification
SPEAKER_IDENTIFICATION_ENABLED=true
SPEAKER_IDENTIFICATION_METHOD=pyannote
HUGGINGFACE_TOKEN=your_hf_token
```

### Production Environment

```bash
# Bind to specific interface
HTTP_HOST=0.0.0.0
HTTP_PORT=8080

# Enable real-time features
REALTIME_API_ENABLED=true
REALTIME_WEBSOCKET_PORT=8081

# Performance logging
LOG_LEVEL=INFO
LOG_FILE=logs/production.log

# Resource limits
REALTIME_MAX_CONNECTIONS=100
```

## 🔒 Security & Deployment

### Security Best Practices

- 🔐 **Environment Variables**: All sensitive data in `.env`
- 🌐 **Local Binding**: Default localhost-only access
- 📝 **Safe Logging**: No sensitive data in logs
- 🧹 **Auto Cleanup**: Temporary files automatically removed
- 🔒 **User Permissions**: Run as non-root user

### SystemD Service

```bash
# Install as system service (included in installation)
sudo systemctl enable whispersilent
sudo systemctl start whispersilent
sudo systemctl status whispersilent

# View logs
sudo journalctl -u whispersilent -f
```

### Docker Deployment

```bash
# Build image
docker build -t whispersilent .

# Run with audio device access
docker run -d --name whispersilent \\
  --device /dev/snd \\
  -p 8080:8080 -p 8081:8081 \\
  -v $(pwd)/transcriptions:/app/transcriptions \\
  -v $(pwd)/.env:/app/.env \\
  whispersilent
```

## 🧪 Comprehensive Testing

### Automated Test Suite

```bash
# Quick validation (< 5 seconds)
python3 scripts/test_microphone_basic.py

# Engine compatibility test
python3 scripts/test_transcription_api.py

# Full system integration (20+ seconds)
python3 scripts/test_complete_system.py

# Installation verification
python3 scripts/validate_installation.py

# Unit tests
python3 -m pytest tests/ -v
```

### Test Coverage

- ✅ **Audio Capture**: Device detection and recording
- ✅ **Speech Recognition**: All 12+ engines tested
- ✅ **Speaker Identification**: All methods validated
- ✅ **Real-time API**: WebSocket functionality
- ✅ **HTTP API**: All endpoints tested
- ✅ **Performance**: Latency and resource usage
- ✅ **Error Handling**: Graceful failure scenarios

## 🐛 Troubleshooting

### Common Issues

#### 🎤 Audio Problems
```bash
# List available devices
python3 scripts/detect_audio_devices.py --list

# Test specific device
python3 scripts/detect_audio_devices.py --test 2

# Check system audio
arecord -l
aplay -l

# Fix permissions
sudo usermod -a -G audio $USER
```

#### 🧠 Model Issues
```bash
# Re-download models
rm -rf models/*.bin
python3 scripts/validate_installation.py

# Check model integrity
ls -la models/
file models/ggml-base.bin
```

#### 🌐 API Connection Problems
```bash
# Test external API
curl -X POST https://your-api.com/transcribe \\
  -H "Content-Type: application/json" \\
  -d '{"test": "connection"}'

# Check logs
tail -f logs/combined.log | grep ERROR
```

#### 💾 Performance Issues
```bash
# Monitor resources
curl http://localhost:8080/health/detailed

# Use smaller model
WHISPER_MODEL_PATH=./models/ggml-tiny.bin

# Reduce processing frequency
CHUNK_DURATION_MS=5000
```

### Diagnostic Tools

```bash
# System health check
curl http://localhost:8080/health

# Real-time metrics
curl http://localhost:8080/health/detailed

# Speaker identification status
curl http://localhost:8080/speakers/statistics

# Real-time API status
curl http://localhost:8080/realtime/status

# View recent logs
tail -f logs/combined.log
```

## 🤝 Contributing

### Development Setup

```bash
# Fork and clone
git clone https://github.com/your-username/whispersilent.git
cd whispersilent

# Development installation
pip install -r requirements.txt
pip install -e .

# Install development tools
pip install pytest black flake8 mypy

# Run tests
python3 -m pytest tests/ -v
```

### Code Standards

- 🐍 **Python**: PEP 8 compliance, type hints preferred
- 📝 **Commits**: Conventional commits (feat, fix, docs, etc.)
- 🧪 **Testing**: pytest for new features
- 📖 **Documentation**: Comprehensive docstrings
- 🔧 **Configuration**: Environment-based settings

### Contribution Workflow

1. **Fork** the repository
2. **Create** feature branch: `git checkout -b feature/amazing-feature`
3. **Develop** with tests and documentation
4. **Test** thoroughly: `python3 scripts/test_complete_system.py`
5. **Commit** with clear messages: `git commit -m 'feat: add amazing feature'`
6. **Push** to branch: `git push origin feature/amazing-feature`
7. **Create** pull request with detailed description

## 🚀 Roadmap

### Upcoming Features

- [ ] 🌍 **Multi-language detection** and automatic switching
- [ ] 📱 **Mobile clients** (iOS/Android apps)
- [ ] ☁️ **Cloud deployment** templates (AWS, GCP, Azure)
- [ ] 🤖 **LLM integration** for post-processing and summarization
- [ ] 📊 **Advanced analytics** with machine learning insights
- [ ] 🔐 **Enterprise features** (authentication, RBAC, audit logs)
- [ ] 🎥 **Video transcription** support
- [ ] 🔄 **Plugin system** for custom extensions

### Community Features

- [ ] 🎪 **Plugin marketplace** for community extensions
- [ ] 🏗️ **Configuration templates** for common use cases
- [ ] 🔗 **Third-party integrations** (Slack, Teams, Discord)
- [ ] 📚 **Community documentation** and tutorials

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **[Whisper.cpp](https://github.com/ggerganov/whisper.cpp)** - Optimized Whisper implementation
- **[OpenAI Whisper](https://github.com/openai/whisper)** - Base transcription model
- **[PyAnnote](https://github.com/pyannote/pyannote-audio)** - Speaker diarization framework
- **[SpeechRecognition](https://github.com/Uberi/speech_recognition)** - Python speech recognition library
- **[Seeed VoiceCard](https://github.com/HinTak/seeed-voicecard)** - Raspberry Pi audio driver

## 📞 Support & Community

- 🐛 **Bug Reports**: [GitHub Issues](https://github.com/your-username/whispersilent/issues)
- 💬 **Discussions**: [GitHub Discussions](https://github.com/your-username/whispersilent/discussions)  
- 📖 **Documentation**: [Project Wiki](https://github.com/your-username/whispersilent/wiki)
- 📧 **Contact**: [Maintainer Email](mailto:maintainer@whispersilent.com)

---

**🎤 WhisperSilent** - Professional real-time transcription with advanced features
*Transform voice to text with precision, intelligence, and scalability*