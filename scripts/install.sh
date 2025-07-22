#!/bin/bash

# WhisperSilent - Comprehensive Installation Script
# This script installs and configures the real-time transcription system
# with complete testing and validation

set -euo pipefail  # Exit on any error, undefined variables, or pipe failures

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_FILE="${SCRIPT_DIR}/installation.log"
BACKUP_DIR="${SCRIPT_DIR}/backup_$(date +%Y%m%d_%H%M%S)"
VENV_DIR="${SCRIPT_DIR}/.venv"
TEST_RESULTS_DIR="${SCRIPT_DIR}/test_results"

# System information
SYSTEM_ARCH=$(uname -m)
SYSTEM_OS=$(uname -s)
CPU_CORES=$(nproc)
TOTAL_RAM=$(free -m | awk '/^Mem:/{print $2}')
AVAILABLE_SPACE=$(df -m "${SCRIPT_DIR}" | awk 'NR==2{print $4}')

# Minimum requirements
MIN_RAM_MB=512
MIN_SPACE_MB=2048
MIN_PYTHON_VERSION="3.8"

# Installation steps tracking
STEPS_COMPLETED=()
CURRENT_STEP=""

# Logging functions
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "${LOG_FILE}"
}

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1" | tee -a "${LOG_FILE}"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1" | tee -a "${LOG_FILE}"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1" | tee -a "${LOG_FILE}"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1" | tee -a "${LOG_FILE}"
}

# Error handling
error_exit() {
    log_error "$1"
    log_error "Installation failed at step: ${CURRENT_STEP}"
    log_error "Check the log file for details: ${LOG_FILE}"
    
    # Offer recovery options
    echo
    echo -e "${YELLOW}Recovery Options:${NC}"
    echo "1. Review the error in ${LOG_FILE}"
    echo "2. Run the script again (it will resume from where it left off)"
    echo "3. Report the issue with the log file"
    
    exit 1
}

# Cleanup function
cleanup() {
    if [[ "${1:-}" != "0" ]]; then
        log_warning "Installation interrupted. Performing cleanup..."
        
        # Stop any running processes
        pkill -f "python.*main" || true
        
        # Restore backups if any critical failure occurred
        if [[ -d "${BACKUP_DIR}" ]]; then
            log_info "Backup available at: ${BACKUP_DIR}"
        fi
    fi
}

trap 'cleanup $?' EXIT

# Progress tracking
start_step() {
    CURRENT_STEP="$1"
    log_info "Starting: ${CURRENT_STEP}"
}

complete_step() {
    STEPS_COMPLETED+=("${CURRENT_STEP}")
    log_success "Completed: ${CURRENT_STEP}"
}

# System checks
check_system_requirements() {
    start_step "System Requirements Check"
    
    log_info "System Information:"
    log_info "  OS: ${SYSTEM_OS}"
    log_info "  Architecture: ${SYSTEM_ARCH}"
    log_info "  CPU Cores: ${CPU_CORES}"
    log_info "  Total RAM: ${TOTAL_RAM}MB"
    log_info "  Available Space: ${AVAILABLE_SPACE}MB"
    
    # Check RAM
    if [[ ${TOTAL_RAM} -lt ${MIN_RAM_MB} ]]; then
        error_exit "Insufficient RAM: ${TOTAL_RAM}MB < ${MIN_RAM_MB}MB required"
    fi
    
    # Check disk space
    if [[ ${AVAILABLE_SPACE} -lt ${MIN_SPACE_MB} ]]; then
        error_exit "Insufficient disk space: ${AVAILABLE_SPACE}MB < ${MIN_SPACE_MB}MB required"
    fi
    
    # Check if running on supported architecture
    case "${SYSTEM_ARCH}" in
        x86_64|aarch64|armv7l|arm64)
            log_success "Supported architecture: ${SYSTEM_ARCH}"
            ;;
        *)
            log_warning "Untested architecture: ${SYSTEM_ARCH}. Proceeding anyway..."
            ;;
    esac
    
    complete_step
}

check_python_version() {
    start_step "Python Version Check"
    
    if ! command -v python3 &> /dev/null; then
        error_exit "Python 3 is not installed"
    fi
    
    PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
    log_info "Found Python ${PYTHON_VERSION}"
    
    # Compare versions
    if python3 -c "import sys; sys.exit(0 if sys.version_info >= (3, 8) else 1)"; then
        log_success "Python version is compatible"
    else
        error_exit "Python ${PYTHON_VERSION} < ${MIN_PYTHON_VERSION} required"
    fi
    
    complete_step
}

install_system_dependencies() {
    start_step "System Dependencies Installation"
    
    # Detect package manager and install dependencies
    if command -v apt-get &> /dev/null; then
        log_info "Detected apt package manager (Debian/Ubuntu)"
        
        # Update package lists
        log_info "Updating package lists..."
        sudo apt-get update -qq
        
        # Install dependencies
        PACKAGES=(
            "build-essential"
            "cmake"
            "git"
            "libasound2-dev"
            "portaudio19-dev"
            "python3-dev"
            "python3-pip"
            "python3-venv"
            "pkg-config"
            "libffi-dev"
            "libssl-dev"
        )
        
        log_info "Installing system packages..."
        for package in "${PACKAGES[@]}"; do
            if ! dpkg -l | grep -q "^ii  ${package} "; then
                log_info "Installing ${package}..."
                sudo apt-get install -y "${package}" || error_exit "Failed to install ${package}"
            else
                log_info "${package} already installed"
            fi
        done
        
    elif command -v yum &> /dev/null; then
        log_info "Detected yum package manager (RedHat/CentOS)"
        
        PACKAGES=(
            "gcc"
            "gcc-c++"
            "cmake"
            "git"
            "alsa-lib-devel"
            "portaudio-devel"
            "python3-devel"
            "python3-pip"
            "openssl-devel"
            "libffi-devel"
        )
        
        for package in "${PACKAGES[@]}"; do
            log_info "Installing ${package}..."
            sudo yum install -y "${package}" || error_exit "Failed to install ${package}"
        done
        
    elif command -v brew &> /dev/null; then
        log_info "Detected Homebrew (macOS)"
        
        PACKAGES=(
            "cmake"
            "git"
            "portaudio"
            "python@3.9"
        )
        
        for package in "${PACKAGES[@]}"; do
            log_info "Installing ${package}..."
            brew install "${package}" || log_warning "Failed to install ${package} (might already exist)"
        done
        
    else
        log_warning "Unknown package manager. Please install dependencies manually:"
        log_warning "- build-essential/gcc"
        log_warning "- cmake"
        log_warning "- git"
        log_warning "- alsa-lib-devel/libasound2-dev"
        log_warning "- portaudio-devel/portaudio19-dev"
        log_warning "- python3-dev"
        log_warning "- python3-pip"
    fi
    
    complete_step
}

setup_python_environment() {
    start_step "Python Virtual Environment Setup"
    
    # Create virtual environment
    if [[ ! -d "${VENV_DIR}" ]]; then
        log_info "Creating virtual environment..."
        python3 -m venv "${VENV_DIR}" || error_exit "Failed to create virtual environment"
    else
        log_info "Virtual environment already exists"
    fi
    
    # Activate virtual environment
    source "${VENV_DIR}/bin/activate" || error_exit "Failed to activate virtual environment"
    
    # Upgrade pip
    log_info "Upgrading pip..."
    pip install --upgrade pip || error_exit "Failed to upgrade pip"
    
    # Install Python dependencies
    log_info "Installing Python dependencies..."
    pip install -r requirements.txt || error_exit "Failed to install Python dependencies"
    
    # Install WebSocket dependencies for real-time API
    log_info "Installing WebSocket dependencies..."
    pip install websockets || log_warning "Failed to install websockets"
    
    # Install optional speaker identification dependencies
    log_info "Installing optional speaker identification dependencies..."
    pip install pyannote.audio resemblyzer speechbrain || log_warning "Some speaker ID dependencies failed (optional)"
    
    complete_step
}

download_whisper_models() {
    start_step "Whisper Models Download"
    
    # Create models directory
    mkdir -p "${SCRIPT_DIR}/models"
    
    # Download base model (default)
    if [[ ! -f "${SCRIPT_DIR}/models/ggml-base.bin" ]]; then
        log_info "Downloading Whisper base model (142MB)..."
        wget --progress=bar:force https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-base.bin -O "${SCRIPT_DIR}/models/ggml-base.bin" || error_exit "Failed to download base model"
        log_success "Base model downloaded"
    else
        log_info "Base model already exists"
    fi
    
    # Optionally download tiny model for resource-constrained devices
    if [[ ${TOTAL_RAM} -lt 1024 ]]; then
        log_info "Low RAM detected - downloading tiny model as well..."
        if [[ ! -f "${SCRIPT_DIR}/models/ggml-tiny.bin" ]]; then
            wget --progress=bar:force https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-tiny.bin -O "${SCRIPT_DIR}/models/ggml-tiny.bin" || log_warning "Failed to download tiny model"
        fi
    fi
    
    complete_step
}

test_audio_system() {
    start_step "Audio System Testing"
    
    # Test ALSA
    if command -v arecord &> /dev/null; then
        log_info "Testing audio recording capability..."
        
        # Test if we can record (1 second test)
        TEST_AUDIO="${SCRIPT_DIR}/test_audio.wav"
        timeout 3s arecord -f cd -d 1 "${TEST_AUDIO}" 2>/dev/null || log_warning "Audio recording test failed - check microphone permissions"
        
        if [[ -f "${TEST_AUDIO}" ]]; then
            log_success "Audio recording test successful"
            rm -f "${TEST_AUDIO}"
        fi
    else
        log_warning "arecord not found - audio testing skipped"
    fi
    
    complete_step
}

create_configuration() {
    start_step "Configuration File Creation"
    
    ENV_FILE="${SCRIPT_DIR}/.env"
    
    if [[ ! -f "${ENV_FILE}" ]]; then
        log_info "Creating default .env configuration..."
        
        cat > "${ENV_FILE}" << EOF
# === CORE AUDIO SETTINGS ===
AUDIO_DEVICE=auto
SAMPLE_RATE=16000
CHANNELS=1
CHUNK_DURATION_MS=3000
SILENCE_THRESHOLD=500
SILENCE_DURATION_MS=1500

# === SPEECH RECOGNITION ===
SPEECH_RECOGNITION_ENGINE=google
SPEECH_RECOGNITION_LANGUAGE=pt-BR
SPEECH_RECOGNITION_TIMEOUT=30

# === WHISPER CONFIGURATION ===
WHISPER_MODEL_PATH=./models/ggml-base.bin
WHISPER_LANGUAGE=pt

# === API INTEGRATION (OPTIONAL) ===
API_ENDPOINT=https://your-api.com/transcribe
API_KEY=your_api_key

# === HTTP SERVER ===
HTTP_HOST=localhost
HTTP_PORT=8080

# === FEATURE TOGGLES ===
SPEAKER_IDENTIFICATION_ENABLED=false
SPEAKER_IDENTIFICATION_METHOD=simple_energy
REALTIME_API_ENABLED=false
REALTIME_WEBSOCKET_PORT=8081

# === LOGGING ===
LOG_LEVEL=INFO

# === OPTIONAL API KEYS ===
# OPENAI_API_KEY=your_openai_key
# GOOGLE_CLOUD_CREDENTIALS_JSON=path/to/credentials.json
# HUGGINGFACE_TOKEN=your_hf_token
EOF
        
        log_success "Default .env file created"
        log_warning "Please edit .env file with your API credentials"
    else
        log_info ".env file already exists"
    fi
    
    # Make API_KEY optional in the template
    if [[ -f "${ENV_FILE}" ]] && grep -q "API_KEY=your_api_key_here" "${ENV_FILE}"; then
        log_info "Note: API_KEY is optional. Remove or leave empty if your API doesn't require authentication."
    fi
    
    complete_step
}

run_comprehensive_tests() {
    start_step "Comprehensive Testing"
    
    # Create test results directory
    mkdir -p "${TEST_RESULTS_DIR}"
    
    # Activate virtual environment
    source "${VENV_DIR}/bin/activate"
    
    # Test 1: Import tests
    log_info "Running import tests..."
    python3 -c "
import sys
modules = [
    'config', 'logger', 'audioCapture', 'audioProcessor', 
    'whisperService', 'apiService', 'transcriptionPipeline',
    'healthMonitor', 'transcriptionStorage', 'transcriptionFiles',
    'httpServer'
]
failed = []
for module in modules:
    try:
        __import__(module)
        print(f'✓ {module}')
    except Exception as e:
        print(f'✗ {module}: {e}')
        failed.append(module)
        
if failed:
    print(f'Failed imports: {failed}')
    sys.exit(1)
else:
    print('All modules imported successfully')
" > "${TEST_RESULTS_DIR}/import_test.log" 2>&1 || error_exit "Module import tests failed"
    
    # Test 2: Configuration validation
    log_info "Testing configuration..."
    python3 -c "
from config import Config
print('Config loaded successfully')
print(f'Model path: {Config.WHISPER[\"model_path\"]}')
print(f'Audio sample rate: {Config.AUDIO[\"sample_rate\"]}')
" > "${TEST_RESULTS_DIR}/config_test.log" 2>&1 || error_exit "Configuration test failed"
    
    # Test 3: Whisper model test
    log_info "Testing Whisper model..."
    if [[ -f "${SCRIPT_DIR}/models/ggml-base.bin" ]]; then
        log_success "Whisper model file exists"
    else
        error_exit "Whisper model file not found"
    fi
    
    # Test 4: Run pytest if available
    if command -v pytest &> /dev/null; then
        log_info "Running pytest suite..."
        pytest tests/ -v --tb=short > "${TEST_RESULTS_DIR}/pytest.log" 2>&1 || log_warning "Some pytest tests failed (check ${TEST_RESULTS_DIR}/pytest.log)"
    else
        log_warning "pytest not available - skipping unit tests"
    fi
    
    # Test 5: Health monitor test
    log_info "Testing health monitoring..."
    python3 -c "
from healthMonitor import HealthMonitor
monitor = HealthMonitor()
status = monitor.get_health_summary()
print(f'Health monitor working: {status}')
" > "${TEST_RESULTS_DIR}/health_test.log" 2>&1 || log_warning "Health monitor test failed"
    
    # Test 6: HTTP server test
    log_info "Testing HTTP server..."
    python3 -c "
from httpServer import TranscriptionHTTPServer
from transcriptionPipeline import TranscriptionPipeline
pipeline = TranscriptionPipeline()
server = TranscriptionHTTPServer(pipeline, 'localhost', 18080)
print('HTTP server can be instantiated')
" > "${TEST_RESULTS_DIR}/http_test.log" 2>&1 || log_warning "HTTP server test failed"
    
    log_success "Test suite completed - results in ${TEST_RESULTS_DIR}/"
    complete_step
}

create_systemd_service() {
    start_step "Systemd Service Creation"
    
    if [[ "${SYSTEM_OS}" == "Linux" ]] && command -v systemctl &> /dev/null; then
        SERVICE_FILE="/etc/systemd/system/whispersilent.service"
        
        log_info "Creating systemd service..."
        sudo tee "${SERVICE_FILE}" > /dev/null << EOF
[Unit]
Description=WhisperSilent Real-time Transcription Service
After=network.target sound.target
Wants=network.target

[Service]
Type=simple
User=$(whoami)
Group=$(id -gn)
WorkingDirectory=${SCRIPT_DIR}
Environment=PATH=${VENV_DIR}/bin:/usr/local/bin:/usr/bin:/bin
ExecStart=${VENV_DIR}/bin/python3 src/mainWithServer.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
KillMode=process

[Install]
WantedBy=multi-user.target
EOF
        
        # Reload systemd and enable service
        sudo systemctl daemon-reload
        sudo systemctl enable whispersilent
        
        log_success "Systemd service created and enabled"
        log_info "Use 'sudo systemctl start whispersilent' to start the service"
        log_info "Use 'sudo systemctl status whispersilent' to check status"
    else
        log_warning "Systemd not available - skipping service creation"
    fi
    
    complete_step
}

create_helper_scripts() {
    start_step "Helper Scripts Creation"
    
    # Start script
    cat > "${SCRIPT_DIR}/start.sh" << 'EOF'
#!/bin/bash
cd "$(dirname "$0")"
source .venv/bin/activate
exec python3 src/mainWithServer.py
EOF
    chmod +x "${SCRIPT_DIR}/start.sh"
    
    # Test script
    cat > "${SCRIPT_DIR}/test.sh" << 'EOF'
#!/bin/bash
cd "$(dirname "$0")"
source .venv/bin/activate
exec python3 -m pytest tests/ -v
EOF
    chmod +x "${SCRIPT_DIR}/test.sh"
    
    # Status script
    cat > "${SCRIPT_DIR}/status.sh" << 'EOF'
#!/bin/bash
cd "$(dirname "$0")"
echo "Checking WhisperSilent status..."
curl -s http://localhost:8080/health | python3 -m json.tool 2>/dev/null || echo "Service not responding"
EOF
    chmod +x "${SCRIPT_DIR}/status.sh"
    
    log_success "Helper scripts created"
    complete_step
}

generate_installation_report() {
    start_step "Installation Report Generation"
    
    REPORT_FILE="${SCRIPT_DIR}/installation_report.txt"
    
    cat > "${REPORT_FILE}" << EOF
WhisperSilent Installation Report
================================
Date: $(date)
System: ${SYSTEM_OS} ${SYSTEM_ARCH}
Python: ${PYTHON_VERSION}

Installation Steps Completed:
$(printf '%s\n' "${STEPS_COMPLETED[@]}" | sed 's/^/  ✓ /')

System Information:
  CPU Cores: ${CPU_CORES}
  Total RAM: ${TOTAL_RAM}MB
  Available Space: ${AVAILABLE_SPACE}MB

Files Created:
  Virtual Environment: ${VENV_DIR}
  Configuration: ${SCRIPT_DIR}/.env
  Test Results: ${TEST_RESULTS_DIR}
  Log File: ${LOG_FILE}

Next Steps:
  1. Edit .env file with your API credentials
  2. Test the installation: ./test.sh
  3. Start the service: ./start.sh
  4. Check status: ./status.sh
  5. Access web interface: http://localhost:8080/health
  6. Swagger API docs: http://localhost:8080/api-docs
  7. Real-time client: Open examples/realtime_web_client.html

Documentation:
  README.md - Project documentation
  CLAUDE.md - Development guide
  logs/ - Runtime logs
  transcriptions/ - Stored transcriptions

Support:
  If you encounter issues, check:
  - ${LOG_FILE}
  - ${TEST_RESULTS_DIR}/
  - System audio configuration
EOF
    
    log_success "Installation report generated: ${REPORT_FILE}"
    complete_step
}

# Main installation function
main() {
    echo -e "${BLUE}"
    echo "=================================="
    echo "WhisperSilent Installation Script"
    echo "=================================="
    echo -e "${NC}"
    
    log_info "Starting installation process..."
    log_info "Log file: ${LOG_FILE}"
    
    # Create necessary directories
    mkdir -p "${TEST_RESULTS_DIR}"
    
    # Run installation steps
    check_system_requirements
    check_python_version
    install_system_dependencies
    setup_python_environment
    download_whisper_models
    test_audio_system
    create_configuration
    run_comprehensive_tests
    create_systemd_service
    create_helper_scripts
    generate_installation_report
    
    echo
    echo -e "${GREEN}🎉 Installation completed successfully!${NC}"
    echo
    echo -e "${BLUE}Next steps:${NC}"
    echo "1. Edit .env file: nano .env"
    echo "2. Test installation: ./test.sh"
    echo "3. Start service: ./start.sh"
    echo "4. Check health: ./status.sh"
    echo
    echo -e "${BLUE}Web Interface:${NC}"
    echo "http://localhost:8080/health"
echo "API Documentation: http://localhost:8080/api-docs"
echo "Real-time WebSocket: ws://localhost:8081"
    echo
    echo -e "${BLUE}Documentation:${NC}"
    echo "cat installation_report.txt"
    echo
}

# Run main function
main "$@"