# Installation Guide

This guide provides detailed installation instructions for WhisperSilent on different platforms.

## Quick Installation

For most users, the automated installation script is recommended:

```bash
# Clone the repository
git clone <repository-url>
cd whispersilent

# Run automated installation and testing
./scripts/install_and_test.sh
```

The script will:
1. Check system dependencies
2. Install Python dependencies
3. Download required models
4. Run validation tests
5. Create service files (optional)

## Manual Installation

### Prerequisites

#### System Dependencies

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install -y python3 python3-pip python3-venv \
    portaudio19-dev alsa-utils build-essential \
    git wget curl
```

**CentOS/RHEL/Fedora:**
```bash
sudo dnf install -y python3 python3-pip python3-venv \
    portaudio-devel alsa-lib-devel gcc gcc-c++ \
    git wget curl
```

**macOS:**
```bash
# Install Homebrew if not installed
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install dependencies
brew install python3 portaudio git wget
```

#### Hardware Requirements

**Minimum:**
- CPU: Raspberry Pi 2W or equivalent (ARM/x86_64)
- RAM: 512MB available
- Storage: 2GB available space
- Audio: USB microphone or audio input device

**Recommended:**
- CPU: 4+ cores, 1.5GHz+
- RAM: 2GB+ available
- Storage: 5GB+ available space
- Audio: Dedicated USB microphone with good SNR

### Step-by-Step Installation

#### 1. Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
# or
venv\Scripts\activate     # Windows
```

#### 2. Install Python Dependencies

```bash
# Basic installation
pip install -r requirements.txt

# Optional: Install specific speech recognition engines
pip install "SpeechRecognition[pocketsphinx]"  # CMU Sphinx (offline)
pip install "SpeechRecognition[vosk]"          # Vosk (offline)
pip install torch torchvision torchaudio      # For neural models
```

#### 3. Download Models

```bash
# Create models directory
mkdir -p models

# Download Whisper model (choose one)
wget https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-base.bin -O models/ggml-base.bin
```

#### 4. Configure Environment

```bash
# Copy example configuration
cp .env.example .env

# Edit configuration
nano .env
```

Required settings:
```bash
# Audio device (auto-detect recommended)
AUDIO_DEVICE=auto

# API endpoints (optional)
API_ENDPOINT=https://your-api.com/transcribe
API_KEY=your_api_key

# Model path
WHISPER_MODEL_PATH=./models/ggml-base.bin
```

#### 5. Audio Device Setup

```bash
# Detect available audio devices
python3 scripts/detect_audio_devices.py --list

# Test specific device
python3 scripts/detect_audio_devices.py --test 2

# Auto-configure (recommended)
python3 scripts/detect_audio_devices.py --auto --update
```

### Advanced Installation Options

#### Speaker Identification Features

For speaker identification, install additional dependencies:

```bash
# PyAnnote (neural speaker diarization)
pip install pyannote.audio

# Resemblyzer (speaker embeddings)
pip install resemblyzer

# SpeechBrain (speaker recognition)
pip install speechbrain
```

Configuration:
```bash
# Enable speaker identification
SPEAKER_IDENTIFICATION_ENABLED=true
SPEAKER_IDENTIFICATION_METHOD=simple_energy  # or pyannote, resemblyzer, speechbrain

# PyAnnote requires HuggingFace token
HUGGINGFACE_TOKEN=your_hf_token
```

#### Real-time WebSocket API

Enable real-time streaming:
```bash
REALTIME_API_ENABLED=true
REALTIME_WEBSOCKET_PORT=8081
```

Install WebSocket dependencies:
```bash
pip install websockets
```

#### Development Installation

For development and testing:

```bash
# Install development dependencies
pip install pytest pytest-cov black flake8 mypy

# Install in development mode
pip install -e .

# Run tests
python -m pytest tests/
```

## Platform-Specific Notes

### Raspberry Pi

For Raspberry Pi installations:

```bash
# Enable audio interface
sudo raspi-config
# -> Advanced Options -> Audio -> Force 3.5mm jack

# Install additional audio tools
sudo apt install -y pulseaudio pulseaudio-utils

# Optimize for Pi
echo "dtparam=audio=on" | sudo tee -a /boot/config.txt
```

For Seeed VoiceCard:
```bash
# Install VoiceCard drivers
git clone https://github.com/respeaker/seeed-voicecard.git
cd seeed-voicecard
sudo ./install.sh
sudo reboot
```

### Docker Installation

Run WhisperSilent in Docker:

```bash
# Build image
docker build -t whispersilent .

# Run container
docker run -d \
  --name whispersilent \
  --device /dev/snd \
  -p 8080:8080 \
  -p 8081:8081 \
  -v $(pwd)/transcriptions:/app/transcriptions \
  -v $(pwd)/.env:/app/.env \
  whispersilent
```

### Service Installation

Install as system service (Linux):

```bash
# Copy service file
sudo cp scripts/whispersilent.service /etc/systemd/system/

# Edit service file with correct paths
sudo nano /etc/systemd/system/whispersilent.service

# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable whispersilent
sudo systemctl start whispersilent

# Check status
sudo systemctl status whispersilent
```

## Verification

After installation, verify the setup:

```bash
# Test microphone
python3 scripts/test_microphone_basic.py

# Test transcription engines
python3 scripts/test_transcription_api.py

# Full system test
python3 scripts/test_complete_system.py

# Start the system
python3 src/mainWithServer.py
```

Check the web interface:
- HTTP API: http://localhost:8080
- Swagger docs: http://localhost:8080/api-docs
- Real-time client: Open `examples/realtime_web_client.html`

## Troubleshooting

### Audio Issues

```bash
# Check audio devices
arecord -l
lsusb | grep -i audio

# Test audio capture
arecord -D plughw:2,0 -f S16_LE -r 16000 -c 1 test.wav -d 5
aplay test.wav
```

### Permission Issues

```bash
# Add user to audio group
sudo usermod -a -G audio $USER

# Set audio device permissions
sudo chmod 666 /dev/snd/*
```

### Python Dependencies

```bash
# Reinstall dependencies
pip install --upgrade --force-reinstall -r requirements.txt

# Clear pip cache
pip cache purge
```

### Model Download Issues

```bash
# Manual model download with progress
wget --progress=bar:force https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-base.bin -O models/ggml-base.bin

# Verify model integrity
ls -la models/
file models/ggml-base.bin
```

## Getting Help

- Check logs: `tail -f logs/combined.log`
- Run diagnostics: `python3 scripts/validate_installation.py`
- Test individual components: See `scripts/README_TESTS.md`
- Open an issue with system info and error logs