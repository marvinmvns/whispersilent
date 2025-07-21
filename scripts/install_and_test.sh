#!/bin/bash

# WhisperSilent Installation and Test Script
# This script automates the complete setup and testing of the whisper transcription system

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script configuration
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN=${PYTHON_BIN:-python3}
PIP_BIN=${PIP_BIN:-pip3}

echo -e "${BLUE}WhisperSilent Installation and Test Script${NC}"
echo "=========================================="
echo "Project root: $PROJECT_ROOT"
echo ""

# Function to print colored messages
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check Python version
check_python_version() {
    print_status "Checking Python version..."
    
    if ! command_exists $PYTHON_BIN; then
        print_error "Python 3 not found. Please install Python 3.7+ and try again."
        exit 1
    fi
    
    python_version=$($PYTHON_BIN --version 2>&1 | awk '{print $2}')
    required_version="3.7"
    
    if $PYTHON_BIN -c "import sys; exit(0 if sys.version_info >= (3, 7) else 1)"; then
        print_success "Python $python_version is compatible"
    else
        print_error "Python $python_version is too old. Please install Python 3.7 or newer."
        exit 1
    fi
}

# Function to install system dependencies
install_system_dependencies() {
    print_status "Installing system dependencies..."
    
    # Detect package manager and install dependencies
    if command_exists apt-get; then
        print_status "Using apt-get package manager"
        sudo apt-get update
        sudo apt-get install -y \
            python3-dev \
            python3-pip \
            python3-venv \
            portaudio19-dev \
            alsa-utils \
            ffmpeg \
            flac \
            git \
            cmake \
            make \
            g++ \
            pkg-config
    elif command_exists yum; then
        print_status "Using yum package manager"
        sudo yum install -y \
            python3-devel \
            python3-pip \
            portaudio-devel \
            alsa-utils \
            ffmpeg \
            flac \
            git \
            cmake \
            make \
            gcc-c++ \
            pkgconfig
    elif command_exists brew; then
        print_status "Using Homebrew package manager"
        brew install \
            portaudio \
            ffmpeg \
            flac \
            git \
            cmake \
            make
    else
        print_warning "Unknown package manager. Please install the following manually:"
        echo "  - portaudio development libraries"
        echo "  - ffmpeg"
        echo "  - flac"
        echo "  - git, cmake, make, gcc/g++"
        echo "  - python3 development headers"
    fi
}

# Function to set up Python virtual environment
setup_virtual_environment() {
    print_status "Setting up Python virtual environment..."
    
    cd "$PROJECT_ROOT"
    
    # Create virtual environment if it doesn't exist
    if [ ! -d "venv" ]; then
        $PYTHON_BIN -m venv venv
        print_success "Virtual environment created"
    else
        print_status "Virtual environment already exists"
    fi
    
    # Activate virtual environment
    source venv/bin/activate
    print_success "Virtual environment activated"
    
    # Upgrade pip
    pip install --upgrade pip setuptools wheel
}

# Function to install Python dependencies
install_python_dependencies() {
    print_status "Installing Python dependencies..."
    
    cd "$PROJECT_ROOT"
    source venv/bin/activate
    
    # Install basic requirements
    pip install -r requirements.txt
    
    # Install optional speech recognition engines based on user choice
    echo ""
    echo "Available speech recognition engines:"
    echo "1. CMU Sphinx (offline)"
    echo "2. Google Cloud Speech API (online, requires credentials)"
    echo "3. Vosk (offline, requires model download)"
    echo "4. Local Whisper (offline)"
    echo "5. Faster Whisper (offline)"
    echo "6. OpenAI Whisper API (online, requires API key)"
    echo "7. Groq Whisper API (online, requires API key)"
    echo "8. Install all offline engines"
    echo "9. Skip optional engines (use basic Google only)"
    echo ""
    
    read -p "Which engines would you like to install? (1-9): " engine_choice
    
    case $engine_choice in
        1)
            print_status "Installing CMU Sphinx..."
            pip install "SpeechRecognition[pocketsphinx]"
            ;;
        2)
            print_status "Installing Google Cloud Speech API..."
            pip install "SpeechRecognition[google-cloud]"
            ;;
        3)
            print_status "Installing Vosk..."
            pip install "SpeechRecognition[vosk]"
            download_vosk_model
            ;;
        4)
            print_status "Installing Local Whisper..."
            pip install "SpeechRecognition[whisper-local]"
            ;;
        5)
            print_status "Installing Faster Whisper..."
            pip install "SpeechRecognition[faster-whisper]"
            ;;
        6)
            print_status "Installing OpenAI Whisper API..."
            pip install "SpeechRecognition[openai]"
            ;;
        7)
            print_status "Installing Groq Whisper API..."
            pip install "SpeechRecognition[groq]"
            ;;
        8)
            print_status "Installing all offline engines..."
            pip install "SpeechRecognition[pocketsphinx]"
            pip install "SpeechRecognition[vosk]"
            pip install "SpeechRecognition[whisper-local]"
            pip install "SpeechRecognition[faster-whisper]"
            download_vosk_model
            ;;
        9)
            print_status "Skipping optional engines"
            ;;
        *)
            print_warning "Invalid choice, skipping optional engines"
            ;;
    esac
    
    print_success "Python dependencies installed"
}

# Function to download Vosk model
download_vosk_model() {
    print_status "Downloading Vosk Portuguese model..."
    
    cd "$PROJECT_ROOT"
    mkdir -p models/vosk
    cd models/vosk
    
    # Download small Portuguese model (about 50MB)
    if [ ! -d "vosk-model-small-pt-0.3" ]; then
        wget https://alphacephei.com/vosk/models/vosk-model-small-pt-0.3.zip
        unzip vosk-model-small-pt-0.3.zip
        rm vosk-model-small-pt-0.3.zip
        print_success "Vosk model downloaded"
    else
        print_status "Vosk model already exists"
    fi
}

# Function to clone and build whisper.cpp (optional for legacy support)
build_whisper_cpp() {
    print_status "Building whisper.cpp (optional for legacy support)..."
    
    cd "$PROJECT_ROOT"
    
    if [ ! -d "whisper.cpp" ]; then
        git clone https://github.com/ggerganov/whisper.cpp.git
    fi
    
    cd whisper.cpp
    git pull  # Update to latest version
    
    # Build with optimizations for Raspberry Pi 2W
    make clean
    make -j$(nproc)
    
    # Download base model if it doesn't exist
    if [ ! -f "models/ggml-base.bin" ]; then
        bash ./models/download-ggml-model.sh base
    fi
    
    print_success "whisper.cpp built successfully"
}

# Function to detect audio devices automatically
detect_audio_devices() {
    print_status "Detecting audio devices automatically..."
    
    cd "$PROJECT_ROOT"
    source venv/bin/activate
    
    # Run audio device detection script
    if $PYTHON_BIN scripts/detect_audio_devices.py --auto --update; then
        print_success "Audio device detection completed"
    else
        print_warning "Audio device detection had issues, using manual configuration"
        manual_audio_device_selection
    fi
}

# Function for manual audio device selection
manual_audio_device_selection() {
    print_status "Manual audio device selection..."
    
    cd "$PROJECT_ROOT"
    source venv/bin/activate
    
    # Show available devices and let user choose
    print_status "Available audio devices:"
    if command_exists arecord; then
        arecord -l
    fi
    
    echo ""
    echo "Audio device configuration options:"
    echo "1. Use automatic detection (recommended)"
    echo "2. Specify device by index (e.g., 2)"
    echo "3. Specify device by name part (e.g., 'USB' or 'seeed')"
    echo "4. Use default Seeed VoiceCard (plughw:2,0)"
    echo ""
    
    read -p "Choose configuration method (1-4): " device_choice
    
    case $device_choice in
        1)
            print_status "Configuring automatic device detection..."
            echo "AUDIO_DEVICE=auto" >> .env
            ;;
        2)
            read -p "Enter device index: " device_index
            echo "AUDIO_DEVICE=$device_index" >> .env
            print_success "Configured device index: $device_index"
            ;;
        3)
            read -p "Enter device name part: " device_name
            echo "AUDIO_DEVICE=$device_name" >> .env
            print_success "Configured device name: $device_name"
            ;;
        4)
            echo "AUDIO_DEVICE=plughw:2,0" >> .env
            print_success "Configured Seeed VoiceCard (plughw:2,0)"
            ;;
        *)
            print_warning "Invalid choice, using automatic detection"
            echo "AUDIO_DEVICE=auto" >> .env
            ;;
    esac
}

# Function to test audio system
test_audio_system() {
    print_status "Testing audio system..."
    
    # Test if ALSA is working
    if command_exists arecord; then
        print_status "Testing basic audio system..."
        arecord -l
        
        # Test if the Seeed VoiceCard is available
        if arecord -l | grep -q "seeed"; then
            print_success "Seeed VoiceCard detected"
        else
            print_warning "Seeed VoiceCard not detected. Will use automatic detection."
        fi
        
        # Run comprehensive audio device detection
        cd "$PROJECT_ROOT"
        source venv/bin/activate
        
        print_status "Running comprehensive audio device test..."
        if $PYTHON_BIN scripts/detect_audio_devices.py --test; then
            print_success "Audio device test successful"
        else
            print_warning "Audio device test had issues. Manual configuration may be needed."
        fi
        
    else
        print_warning "arecord not found. Audio testing skipped."
    fi
}

# Function to test speech recognition engines
test_speech_recognition() {
    print_status "Testing speech recognition engines..."
    
    cd "$PROJECT_ROOT"
    source venv/bin/activate
    
    # Create test script
    cat > test_engines.py << 'EOF'
import sys
import os
sys.path.append('src/core')
sys.path.append('src/transcription')

from speechRecognitionService import SpeechRecognitionService, TranscriptionEngine
from config import Config
import numpy as np

def test_engine(engine_name):
    """Test a specific speech recognition engine"""
    print(f"\n=== Testing {engine_name} ===")
    
    # Set environment variable for testing
    os.environ['SPEECH_RECOGNITION_ENGINE'] = engine_name
    
    # Reload config
    import importlib
    import config
    importlib.reload(config)
    
    try:
        service = SpeechRecognitionService()
        engine_info = service.get_engine_info()
        
        print(f"Engine: {engine_info['engine']}")
        print(f"Language: {engine_info['language']}")
        print(f"Offline: {engine_info['offline']}")
        print(f"Requires API Key: {engine_info['requires_api_key']}")
        print(f"Status: {engine_info['status']}")
        
        # Create sample audio (silent, just for testing initialization)
        sample_rate = 16000
        duration = 1
        audio_data = np.zeros(sample_rate * duration, dtype=np.int16)
        
        # Test transcription (will likely return empty for silent audio)
        result = service.transcribe(audio_data)
        print(f"Test result: '{result}' (empty expected for silent audio)")
        
        return True
        
    except Exception as e:
        print(f"Error testing {engine_name}: {e}")
        return False

# Test available engines
engines_to_test = ['google']  # Always available

# Test other engines if dependencies are installed
optional_engines = {
    'sphinx': 'pocketsphinx',
    'vosk': 'vosk',
    'whisper_local': 'whisper',
    'faster_whisper': 'faster_whisper'
}

for engine, package in optional_engines.items():
    try:
        __import__(package)
        engines_to_test.append(engine)
    except ImportError:
        print(f"Skipping {engine} (package {package} not installed)")

print(f"Testing {len(engines_to_test)} engines: {engines_to_test}")

for engine in engines_to_test:
    try:
        test_engine(engine)
    except Exception as e:
        print(f"Failed to test {engine}: {e}")

print("\n=== Speech Recognition Test Complete ===")
EOF

    $PYTHON_BIN test_engines.py
    rm test_engines.py
}

# Function to create .env file from example
setup_environment_file() {
    print_status "Setting up environment configuration..."
    
    cd "$PROJECT_ROOT"
    
    if [ ! -f ".env" ]; then
        cp .env.example .env
        print_success ".env file created from example"
        print_warning "Please edit .env file to configure your API keys and settings"
        
        # Set default to Google (free) engine
        sed -i 's/SPEECH_RECOGNITION_ENGINE=google/SPEECH_RECOGNITION_ENGINE=google/' .env
        
        echo ""
        echo "Quick setup recommendations:"
        echo "1. For Raspberry Pi 2W: Use 'google' engine (free, requires internet)"
        echo "2. For offline use: Install and use 'sphinx' or 'vosk' engine"
        echo "3. For best quality: Use 'whisper_local' engine (requires more CPU)"
        echo ""
    else
        print_status ".env file already exists"
    fi
}

# Function to run comprehensive system tests
run_system_test() {
    print_status "Running comprehensive system tests..."
    
    cd "$PROJECT_ROOT"
    source venv/bin/activate
    
    # Test 1: Module imports
    print_status "Testing module imports..."
    $PYTHON_BIN -c "
import sys
sys.path.append('src/core')
sys.path.append('src/transcription')
sys.path.append('src/api')
sys.path.append('src/services')

from config import Config
from speechRecognitionService import SpeechRecognitionService
from transcriptionPipeline import TranscriptionPipeline
print('All imports successful!')
"
    
    if [ $? -eq 0 ]; then
        print_success "Module import test passed"
    else
        print_error "Module import test failed"
        return 1
    fi
    
    # Test 2: Configuration
    print_status "Testing configuration..."
    $PYTHON_BIN -c "
import sys
sys.path.append('src/core')
from config import Config
print(f'Audio sample rate: {Config.AUDIO[\"sample_rate\"]}')
print(f'Speech engine: {Config.SPEECH_RECOGNITION[\"engine\"]}')
print('Configuration test passed!')
"
    
    # Test 3: Basic microphone test
    print_status "Running basic microphone test..."
    if $PYTHON_BIN scripts/test_microphone_basic.py; then
        print_success "Basic microphone test passed"
    else
        print_warning "Basic microphone test had issues - check device configuration"
    fi
    
    # Test 4: Transcription API test
    print_status "Running transcription API test..."
    if $PYTHON_BIN scripts/test_transcription_api.py; then
        print_success "Transcription API test passed"
    else
        print_warning "Transcription API test had issues - check configuration"
    fi
    
    print_success "System test completed successfully"
}

# Function to display final setup instructions
show_final_instructions() {
    print_success "Installation completed successfully!"
    
    echo ""
    echo "=========================================="
    echo "           SETUP COMPLETE"
    echo "=========================================="
    echo ""
    echo "Next steps:"
    echo ""
    echo "1. Edit the .env file to configure your settings:"
    echo "   nano .env"
    echo ""
    echo "2. Choose your speech recognition engine in .env:"
    echo "   - google: Free, requires internet, good quality"
    echo "   - sphinx: Offline, moderate quality"
    echo "   - vosk: Offline, good quality"
    echo "   - whisper_local: Offline, best quality, high CPU usage"
    echo ""
    echo "3. For Raspberry Pi with Seeed VoiceCard, verify audio device:"
    echo "   arecord -l"
    echo ""
    echo "4. Run comprehensive system test (optional):"
    echo "   python scripts/test_complete_system.py"
    echo ""
    echo "5. Start the transcription system:"
    echo "   cd $PROJECT_ROOT"
    echo "   source venv/bin/activate"
    echo "   python src/mainWithServer.py"
    echo ""
    echo "6. Access the web interface:"
    echo "   http://localhost:8000"
    echo ""
    echo "Available test scripts:"
    echo "   - scripts/test_microphone_basic.py (quick microphone test)"
    echo "   - scripts/test_transcription_api.py (transcription engines test)"
    echo "   - scripts/test_complete_system.py (full system test)"
    echo ""
    echo "For help and documentation, see:"
    echo "   - CLAUDE.md (project documentation)"
    echo "   - README.md (general information)"
    echo "   - logs/ directory (runtime logs)"
    echo ""
}

# Main installation process
main() {
    echo "Starting WhisperSilent installation..."
    echo ""
    
    # Ask user what to install
    echo "Installation options:"
    echo "1. Full installation (recommended)"
    echo "2. Python dependencies only"
    echo "3. System dependencies only"
    echo "4. Test existing installation"
    echo ""
    
    read -p "Select installation type (1-4): " install_type
    
    case $install_type in
        1)
            print_status "Starting full installation..."
            check_python_version
            install_system_dependencies
            setup_virtual_environment
            install_python_dependencies
            setup_environment_file
            detect_audio_devices
            test_audio_system
            test_speech_recognition
            run_system_test
            show_final_instructions
            ;;
        2)
            print_status "Installing Python dependencies only..."
            check_python_version
            setup_virtual_environment
            install_python_dependencies
            setup_environment_file
            test_speech_recognition
            run_system_test
            print_success "Python installation completed"
            ;;
        3)
            print_status "Installing system dependencies only..."
            install_system_dependencies
            test_audio_system
            print_success "System dependencies installed"
            ;;
        4)
            print_status "Testing existing installation..."
            check_python_version
            cd "$PROJECT_ROOT"
            if [ -d "venv" ]; then
                source venv/bin/activate
            fi
            test_audio_system
            test_speech_recognition
            run_system_test
            
            # Ask if user wants to run comprehensive test
            echo ""
            read -p "Run comprehensive system test? (y/N): " run_comprehensive
            if [[ $run_comprehensive =~ ^[Yy]$ ]]; then
                print_status "Running comprehensive system test..."
                $PYTHON_BIN scripts/test_complete_system.py
            fi
            
            print_success "Installation test completed"
            ;;
        *)
            print_error "Invalid choice"
            exit 1
            ;;
    esac
}

# Check if script is run directly or sourced
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi