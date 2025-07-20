import os
import sys
import subprocess
import requests
import platform
import shutil
from tqdm import tqdm

MODELS = {
    "tiny": {"url": "https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-tiny.bin", "size": "39 MB"},
    "base": {"url": "https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-base.bin", "size": "142 MB"},
    "small": {"url": "https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-small.bin", "size": "466 MB"},
}

MODELS_DIR = os.path.join(os.path.dirname(__file__), "models")

def detect_system_info():
    """Detect system architecture and capabilities"""
    info = {
        "system": platform.system(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "architecture": platform.architecture()[0],
        "cpu_count": os.cpu_count(),
        "has_cuda": False,
        "has_opencl": False,
        "has_metal": False,
        "optimal_threads": min(4, os.cpu_count() or 4)
    }
    
    # Check for GPU capabilities
    try:
        # Check for NVIDIA CUDA
        result = subprocess.run(["nvidia-smi"], capture_output=True, text=True)
        if result.returncode == 0:
            info["has_cuda"] = True
            print("✓ NVIDIA CUDA detected")
    except FileNotFoundError:
        pass
        
    try:
        # Check for OpenCL
        result = subprocess.run(["clinfo"], capture_output=True, text=True)
        if result.returncode == 0:
            info["has_opencl"] = True
            print("✓ OpenCL detected")
    except FileNotFoundError:
        pass
        
    # Check for Metal (macOS)
    if info["system"] == "Darwin":
        info["has_metal"] = True
        print("✓ Metal support available (macOS)")
        
    print(f"System: {info['system']} {info['architecture']}")
    print(f"CPU: {info['machine']} ({info['cpu_count']} cores)")
    print(f"Optimal threads: {info['optimal_threads']}")
    
    return info

def get_whisper_cpp_build_flags(system_info):
    """Get optimal build flags for whisper.cpp based on system"""
    flags = []
    
    # Basic optimization flags
    flags.extend(["-O3", "-march=native"])
    
    # GPU acceleration flags
    if system_info["has_cuda"]:
        flags.append("-DGGML_USE_CUDA=ON")
        print("Adding CUDA support to build")
        
    if system_info["has_opencl"]:
        flags.append("-DGGML_USE_OPENCL=ON")
        print("Adding OpenCL support to build")
        
    if system_info["has_metal"]:
        flags.append("-DGGML_USE_METAL=ON")
        print("Adding Metal support to build")
        
    # ARM-specific optimizations
    if "arm" in system_info["machine"].lower() or "aarch64" in system_info["machine"].lower():
        flags.append("-DGGML_USE_NEON=ON")
        print("Adding ARM NEON optimizations")
        
    # x86 optimizations
    if "x86" in system_info["machine"].lower():
        flags.extend(["-DGGML_USE_AVX=ON", "-DGGML_USE_AVX2=ON", "-DGGML_USE_F16C=ON"])
        print("Adding x86 AVX/AVX2 optimizations")
        
    return flags

def check_dependencies():
    """Check for required build dependencies"""
    dependencies = {
        "git": "git --version",
        "make": "make --version",
        "gcc": "gcc --version",
        "cmake": "cmake --version"
    }
    
    missing = []
    for dep, cmd in dependencies.items():
        try:
            subprocess.run(cmd.split(), capture_output=True, check=True)
            print(f"✓ {dep} found")
        except (subprocess.CalledProcessError, FileNotFoundError):
            missing.append(dep)
            print(f"✗ {dep} missing")
            
    if missing:
        print(f"\nMissing dependencies: {', '.join(missing)}")
        print("Please install missing dependencies:")
        if "cmake" in missing:
            print("  sudo apt-get install cmake")
        if "make" in missing:
            print("  sudo apt-get install build-essential")
        if "gcc" in missing:
            print("  sudo apt-get install gcc")
        if "git" in missing:
            print("  sudo apt-get install git")
        return False
        
    return True

def download_precompiled_binary(system_info):
    """Try to download precompiled binary if available"""
    # This is a placeholder for future implementation
    # Could check for precompiled binaries for common architectures
    
    binary_urls = {
        ("Linux", "x86_64"): None,  # Add URLs when available
        ("Linux", "aarch64"): None,
        ("Darwin", "x86_64"): None,
        ("Darwin", "arm64"): None,
        ("Windows", "AMD64"): None
    }
    
    key = (system_info["system"], system_info["machine"])
    if key in binary_urls and binary_urls[key]:
        print(f"Precompiled binary available for {key[0]} {key[1]}")
        # Implementation would download and extract binary
        return True
        
    return False

def download_model(model_name="base"):
    if model_name not in MODELS:
        print(f"Erro: Modelo '{model_name}' não encontrado. Modelos disponíveis: {list(MODELS.keys())}")
        sys.exit(1)

    model_info = MODELS[model_name]
    model_url = model_info["url"]
    model_size = model_info["size"]
    model_filename = os.path.basename(model_url)
    model_path = os.path.join(MODELS_DIR, model_filename)

    os.makedirs(MODELS_DIR, exist_ok=True)

    if os.path.exists(model_path):
        print(f"Modelo '{model_filename}' já existe em {MODELS_DIR}. Pulando download.")
        return

    print(f"Baixando modelo '{model_filename}' ({model_size})...")
    try:
        response = requests.get(model_url, stream=True)
        response.raise_for_status()

        total_size = int(response.headers.get('content-length', 0))
        block_size = 1024 # 1 Kibibyte

        with open(model_path, 'wb') as f:
            with tqdm(total=total_size, unit='iB', unit_scale=True, desc=model_filename) as pbar:
                for data in response.iter_content(block_size):
                    f.write(data)
                    pbar.update(len(data))
        print(f"Download de '{model_filename}' concluído com sucesso!")
    except requests.exceptions.RequestException as e:
        print(f"Erro ao baixar o modelo: {e}")
        if os.path.exists(model_path):
            os.remove(model_path) # Clean up incomplete download
        sys.exit(1)

def compile_whisper_cpp():
    print("=== Compilando whisper.cpp ===")
    
    # Detect system capabilities
    system_info = detect_system_info()
    
    # Check dependencies
    if not check_dependencies():
        print("Dependências faltando. Instale-as antes de continuar.")
        sys.exit(1)
    
    whisper_cpp_dir = os.path.join(os.path.dirname(__file__), "whisper.cpp")
    
    # Try to download precompiled binary first
    if download_precompiled_binary(system_info):
        print("Usando binário pré-compilado.")
        return
    
    # Clone repository if not exists
    if not os.path.exists(whisper_cpp_dir):
        print("Clonando repositório whisper.cpp...")
        try:
            subprocess.run(["git", "clone", "https://github.com/ggerganov/whisper.cpp.git", whisper_cpp_dir], check=True)
            print("Repositório whisper.cpp clonado com sucesso.")
        except subprocess.CalledProcessError as e:
            print(f"Erro ao clonar whisper.cpp: {e}")
            sys.exit(1)
    
    # Use CMake for better optimization control
    build_dir = os.path.join(whisper_cpp_dir, "build")
    os.makedirs(build_dir, exist_ok=True)
    
    print("Configurando build com CMake...")
    cmake_args = ["cmake", "..", "-DCMAKE_BUILD_TYPE=Release"]
    
    # Add architecture-specific flags
    build_flags = get_whisper_cpp_build_flags(system_info)
    cmake_args.extend(build_flags)
    
    # Set optimal number of threads
    cmake_args.append(f"-DCMAKE_BUILD_PARALLEL_LEVEL={system_info['optimal_threads']}")
    
    try:
        subprocess.run(cmake_args, cwd=build_dir, check=True)
        print("Configuração CMake concluída.")
    except subprocess.CalledProcessError as e:
        print(f"Erro na configuração CMake: {e}")
        print("Tentando fallback para Makefile...")
        
        # Fallback to traditional make
        try:
            make_jobs = min(system_info["cpu_count"] or 4, 4)  # Limit for Raspberry Pi
            subprocess.run(["make", "-C", whisper_cpp_dir, f"-j{make_jobs}"], check=True)
            print("whisper.cpp compilado com sucesso usando Makefile.")
            return
        except subprocess.CalledProcessError as make_error:
            print(f"Erro ao compilar com make: {make_error}")
            sys.exit(1)
    
    print("Compilando whisper.cpp...")
    try:
        subprocess.run(["cmake", "--build", ".", f"-j{system_info['optimal_threads']}"], 
                      cwd=build_dir, check=True)
        print("whisper.cpp compilado com sucesso usando CMake.")
        
        # Create symlink to main executable for compatibility
        main_exe = os.path.join(build_dir, "bin", "main")
        if os.path.exists(main_exe):
            symlink_path = os.path.join(whisper_cpp_dir, "main")
            if not os.path.exists(symlink_path):
                os.symlink(main_exe, symlink_path)
                print(f"Criado symlink: {symlink_path}")
                
    except subprocess.CalledProcessError as e:
        print(f"Erro ao compilar whisper.cpp: {e}")
        sys.exit(1)
        
    # Verify compilation
    executable_paths = [
        os.path.join(build_dir, "bin", "main"),
        os.path.join(whisper_cpp_dir, "main")
    ]
    
    executable_found = False
    for path in executable_paths:
        if os.path.exists(path) and os.access(path, os.X_OK):
            print(f"✓ Executável whisper encontrado: {path}")
            executable_found = True
            break
            
    if not executable_found:
        print("✗ Executável whisper não encontrado após compilação!")
        sys.exit(1)
        
    print("=== Compilação concluída ===")
    print(f"Sistema: {system_info['system']} {system_info['machine']}")
    print(f"Threads utilizadas: {system_info['optimal_threads']}")
    if system_info['has_cuda']:
        print("✓ Suporte CUDA ativado")
    if system_info['has_opencl']:
        print("✓ Suporte OpenCL ativado")
    if system_info['has_metal']:
        print("✓ Suporte Metal ativado")

if __name__ == "__main__":
    model_to_download = "base"
    if len(sys.argv) > 1:
        model_to_download = sys.argv[1]
    
    compile_whisper_cpp()
    download_model(model_to_download)
