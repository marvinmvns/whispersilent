#!/bin/bash
# 🧪 WhisperSilent - Comprehensive Test Suite
# Centralizes all tests with interactive menu system
# Author: Claude Code
# Version: 1.0

set -e  # Exit on any error

# Colors for better output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
NC='\033[0m' # No Color

# Global variables
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
PYTHON_CMD="python3"
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0
TEST_RESULTS=()

# Logging functions
log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

log_header() {
    echo -e "${PURPLE}🔬 $1${NC}"
    echo -e "${PURPLE}$(echo "$1" | sed 's/./=/g')${NC}"
}

# Function to check if a file exists
check_file() {
    if [[ ! -f "$1" ]]; then
        log_error "File not found: $1"
        return 1
    fi
    return 0
}

# Function to run a test and track results
run_test() {
    local test_name="$1"
    local test_command="$2"
    local description="$3"
    local timeout_duration="${4:-120}"  # Default 2 minutes timeout
    
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    
    echo ""
    log_header "TEST: $test_name"
    log_info "$description"
    echo ""
    
    local start_time=$(date +%s)
    local success=false
    
    # Run the test with timeout
    if timeout "$timeout_duration" bash -c "$test_command"; then
        local end_time=$(date +%s)
        local duration=$((end_time - start_time))
        log_success "Test passed in ${duration}s: $test_name"
        PASSED_TESTS=$((PASSED_TESTS + 1))
        TEST_RESULTS+=("✅ PASS - $test_name (${duration}s)")
        success=true
    else
        local end_time=$(date +%s)
        local duration=$((end_time - start_time))
        log_error "Test failed after ${duration}s: $test_name"
        FAILED_TESTS=$((FAILED_TESTS + 1))
        TEST_RESULTS+=("❌ FAIL - $test_name (${duration}s)")
    fi
    
    echo ""
    read -p "Press Enter to continue..." -r
    return $([[ "$success" == "true" ]] && echo 0 || echo 1)
}

# Individual test functions
test_installation_validation() {
    run_test "Installation Validation" \
        "cd '$PROJECT_ROOT' && $PYTHON_CMD scripts/validate_installation.py" \
        "Validates complete system installation and dependencies" \
        180
}

test_microphone_basic() {
    run_test "Basic Microphone Test" \
        "cd '$PROJECT_ROOT' && $PYTHON_CMD scripts/test_microphone_basic.py" \
        "Quick 2-second microphone capture test" \
        30
}

test_microphone_capture() {
    run_test "Microphone Capture Test" \
        "cd '$PROJECT_ROOT' && $PYTHON_CMD scripts/test_microphone_capture.py" \
        "Extended microphone capture and audio analysis" \
        60
}

test_transcription_api() {
    run_test "Transcription API Test" \
        "cd '$PROJECT_ROOT' && $PYTHON_CMD scripts/test_transcription_api.py" \
        "Tests all available speech recognition engines" \
        300
}

test_complete_system() {
    run_test "Complete System Test" \
        "cd '$PROJECT_ROOT' && timeout 25 $PYTHON_CMD scripts/test_complete_system.py || true" \
        "Full integration test with real-time audio processing (20+ seconds)" \
        45
}

test_json_transcriber() {
    run_test "JSON Transcriber Test" \
        "cd '$PROJECT_ROOT' && timeout 15 $PYTHON_CMD scripts/test_json_transcriber.py || true" \
        "JSON transcriber functionality test" \
        30
}

test_json_simple() {
    run_test "JSON Simple Test" \
        "cd '$PROJECT_ROOT' && timeout 10 $PYTHON_CMD test_json_simple.py || true" \
        "Simple JSON transcriber test from project root" \
        25
}

test_main_files_structure() {
    run_test "Main Files Structure" \
        "cd '$PROJECT_ROOT' && $PYTHON_CMD scripts/validate_main_files.py" \
        "Validates main.py and mainWithServer.py structure and patterns" \
        30
}

test_main_files_basic() {
    run_test "Main Files Basic Functionality" \
        "cd '$PROJECT_ROOT' && $PYTHON_CMD scripts/test_main_files_basic.py" \
        "Tests basic startup functionality of main files" \
        45
}

test_http_endpoints() {
    run_test "HTTP Endpoints Test" \
        "cd '$PROJECT_ROOT' && $PYTHON_CMD scripts/test_http_endpoints.py" \
        "Comprehensive test of all HTTP API endpoints" \
        180
}

test_audio_device_detection() {
    run_test "Audio Device Detection" \
        "cd '$PROJECT_ROOT' && $PYTHON_CMD scripts/detect_audio_devices.py --list" \
        "Lists and validates available audio devices" \
        30
}

test_pytest_suite() {
    run_test "Pytest Suite" \
        "cd '$PROJECT_ROOT' && $PYTHON_CMD -m pytest tests/ -v --tb=short" \
        "Runs all pytest unit and integration tests" \
        120
}

# Menu functions
show_main_menu() {
    clear
    echo -e "${CYAN}"
    echo "🎤 WHISPERSILENT - COMPREHENSIVE TEST SUITE"
    echo "============================================="
    echo -e "${NC}"
    echo -e "${WHITE}Select test category or option:${NC}"
    echo ""
    echo -e "${GREEN} 1) 🚀 Quick Tests (Essential)${NC}"
    echo -e "${BLUE} 2) 🔧 Installation & Setup Tests${NC}"
    echo -e "${YELLOW} 3) 🎙️  Audio & Microphone Tests${NC}"
    echo -e "${PURPLE} 4) 🗣️  Transcription Tests${NC}"
    echo -e "${CYAN} 5) 🌐 System & HTTP Tests${NC}"
    echo -e "${WHITE} 6) 🧪 Complete Test Suite (All)${NC}"
    echo ""
    echo -e "${GREEN} 7) 📋 Individual Test Menu${NC}"
    echo -e "${BLUE} 8) 📊 Run Custom Test Sequence${NC}"
    echo ""
    echo -e "${RED} 0) 🚪 Exit${NC}"
    echo ""
    echo -e "${YELLOW}Current directory: $(pwd)${NC}"
    echo -e "${YELLOW}Python command: $PYTHON_CMD${NC}"
    echo ""
}

show_individual_menu() {
    clear
    echo -e "${CYAN}📋 INDIVIDUAL TESTS MENU${NC}"
    echo "=========================="
    echo ""
    echo -e "${WHITE}Select individual test to run:${NC}"
    echo ""
    echo -e "${GREEN} 1) Installation Validation${NC}"
    echo -e "${GREEN} 2) Basic Microphone Test${NC}"
    echo -e "${GREEN} 3) Microphone Capture Test${NC}"
    echo -e "${BLUE} 4) Audio Device Detection${NC}"
    echo -e "${YELLOW} 5) Transcription API Test${NC}"
    echo -e "${YELLOW} 6) JSON Transcriber Test${NC}"
    echo -e "${YELLOW} 7) JSON Simple Test${NC}"
    echo -e "${PURPLE} 8) Complete System Test${NC}"
    echo -e "${CYAN} 9) Main Files Structure${NC}"
    echo -e "${CYAN}10) Main Files Basic Functionality${NC}"
    echo -e "${WHITE}11) HTTP Endpoints Test${NC}"
    echo -e "${BLUE}12) Pytest Suite${NC}"
    echo ""
    echo -e "${RED} 0) 🔙 Back to Main Menu${NC}"
    echo ""
}

# Test suite functions
run_quick_tests() {
    log_header "QUICK TESTS - Essential Validation"
    test_installation_validation
    test_microphone_basic
    test_main_files_structure
    show_test_summary
}

run_installation_tests() {
    log_header "INSTALLATION & SETUP TESTS"
    test_installation_validation
    test_audio_device_detection
    test_main_files_structure
    test_main_files_basic
    show_test_summary
}

run_audio_tests() {
    log_header "AUDIO & MICROPHONE TESTS"
    test_audio_device_detection
    test_microphone_basic
    test_microphone_capture
    show_test_summary
}

run_transcription_tests() {
    log_header "TRANSCRIPTION TESTS"
    test_transcription_api
    test_json_transcriber
    test_json_simple
    test_complete_system
    show_test_summary
}

run_system_tests() {
    log_header "SYSTEM & HTTP TESTS"
    test_main_files_basic
    test_http_endpoints
    test_pytest_suite
    show_test_summary
}

run_complete_suite() {
    log_header "COMPLETE TEST SUITE - ALL TESTS"
    
    # Installation & Setup
    test_installation_validation
    test_audio_device_detection
    
    # Audio Tests
    test_microphone_basic
    test_microphone_capture
    
    # Structure Tests
    test_main_files_structure
    test_main_files_basic
    
    # Transcription Tests
    test_transcription_api
    test_json_transcriber
    test_json_simple
    
    # System Tests
    test_complete_system
    test_http_endpoints
    
    # Unit Tests
    test_pytest_suite
    
    show_test_summary
}

# Summary function
show_test_summary() {
    echo ""
    log_header "TEST SUMMARY REPORT"
    echo ""
    echo -e "${WHITE}📊 Overall Results:${NC}"
    echo -e "   Total Tests: ${WHITE}$TOTAL_TESTS${NC}"
    echo -e "   ${GREEN}Passed: $PASSED_TESTS${NC}"
    echo -e "   ${RED}Failed: $FAILED_TESTS${NC}"
    
    if [[ $TOTAL_TESTS -gt 0 ]]; then
        local success_rate=$((PASSED_TESTS * 100 / TOTAL_TESTS))
        echo -e "   Success Rate: ${WHITE}${success_rate}%${NC}"
    fi
    
    echo ""
    echo -e "${WHITE}📋 Detailed Results:${NC}"
    for result in "${TEST_RESULTS[@]}"; do
        echo -e "   $result"
    done
    
    echo ""
    if [[ $FAILED_TESTS -eq 0 ]]; then
        log_success "🎉 ALL TESTS PASSED! System is working correctly."
    else
        log_warning "⚠️  Some tests failed. Check the results above."
    fi
    
    echo ""
    echo -e "${CYAN}💡 Next Steps:${NC}"
    if [[ $FAILED_TESTS -eq 0 ]]; then
        echo "   • System is ready for production use"
        echo "   • Run: python3 src/main.py (basic transcription)"
        echo "   • Run: python3 src/mainWithServer.py (with HTTP API)"
    else
        echo "   • Fix failed tests by checking error messages"
        echo "   • Install missing dependencies: pip install -r requirements.txt"
        echo "   • Check .env configuration"
        echo "   • Verify audio device setup"
    fi
    
    echo ""
    read -p "Press Enter to continue..." -r
}

# Custom test sequence
run_custom_sequence() {
    clear
    echo -e "${CYAN}📊 CUSTOM TEST SEQUENCE${NC}"
    echo "======================="
    echo ""
    echo "Enter test numbers separated by spaces (e.g., 1 2 5 8):"
    echo "1=Installation 2=Microphone 3=Capture 4=Audio-Device"
    echo "5=Transcription-API 6=JSON-Transcriber 7=JSON-Simple"
    echo "8=Complete-System 9=Structure 10=Basic-Functionality"
    echo "11=HTTP-Endpoints 12=Pytest"
    echo ""
    read -p "Test sequence: " -r sequence
    
    log_header "CUSTOM TEST SEQUENCE: $sequence"
    
    for test_num in $sequence; do
        case $test_num in
            1) test_installation_validation ;;
            2) test_microphone_basic ;;
            3) test_microphone_capture ;;
            4) test_audio_device_detection ;;
            5) test_transcription_api ;;
            6) test_json_transcriber ;;
            7) test_json_simple ;;
            8) test_complete_system ;;
            9) test_main_files_structure ;;
            10) test_main_files_basic ;;
            11) test_http_endpoints ;;
            12) test_pytest_suite ;;
            *) log_warning "Unknown test number: $test_num" ;;
        esac
    done
    
    show_test_summary
}

# Initialization
initialize() {
    cd "$PROJECT_ROOT"
    
    # Check if we're in the right directory
    if [[ ! -f "src/main.py" ]]; then
        log_error "Not in WhisperSilent project directory!"
        log_info "Please run this script from the project root."
        exit 1
    fi
    
    # Check Python availability
    if ! command -v $PYTHON_CMD &> /dev/null; then
        log_error "Python3 not found!"
        exit 1
    fi
    
    log_info "Initialized in: $(pwd)"
    log_info "Python version: $($PYTHON_CMD --version)"
}

# Main loop
main() {
    initialize
    
    while true; do
        show_main_menu
        read -p "Enter your choice: " -r choice
        
        case $choice in
            1) run_quick_tests ;;
            2) run_installation_tests ;;
            3) run_audio_tests ;;
            4) run_transcription_tests ;;
            5) run_system_tests ;;
            6) run_complete_suite ;;
            7)
                while true; do
                    show_individual_menu
                    read -p "Enter your choice: " -r individual_choice
                    
                    case $individual_choice in
                        1) test_installation_validation ;;
                        2) test_microphone_basic ;;
                        3) test_microphone_capture ;;
                        4) test_audio_device_detection ;;
                        5) test_transcription_api ;;
                        6) test_json_transcriber ;;
                        7) test_json_simple ;;
                        8) test_complete_system ;;
                        9) test_main_files_structure ;;
                        10) test_main_files_basic ;;
                        11) test_http_endpoints ;;
                        12) test_pytest_suite ;;
                        0) break ;;
                        *) log_error "Invalid choice!" ;;
                    esac
                done
                ;;
            8) run_custom_sequence ;;
            0) 
                echo ""
                log_success "Thank you for using WhisperSilent Test Suite!"
                exit 0
                ;;
            *) log_error "Invalid choice!" ;;
        esac
        
        # Reset counters for next test run
        TOTAL_TESTS=0
        PASSED_TESTS=0
        FAILED_TESTS=0
        TEST_RESULTS=()
    done
}

# Handle script interruption
trap 'echo -e "\n${YELLOW}⚡ Test interrupted by user${NC}"; exit 130' INT

# Run main function
main "$@"