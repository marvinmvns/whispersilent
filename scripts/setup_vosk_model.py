#!/usr/bin/env python3
"""
Vosk Model Setup Script
Automatically downloads and configures Vosk model for offline transcription
"""

import os
import sys
import zipfile
import requests
from pathlib import Path
import json

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src', 'core'))
from logger import log

# Vosk model URLs (Portuguese and English)
# Default: Portuguese small model (optimized for Brazilian Portuguese)
VOSK_MODELS = {
    'pt': {
        'small': {
            'url': 'https://alphacephei.com/vosk/models/vosk-model-small-pt-0.3.zip',
            'size': '39MB',
            'description': 'Portuguese small model (fastest, Brazilian Portuguese optimized)',
            'default': True  # Default choice for automated installation
        },
        'large': {
            'url': 'https://alphacephei.com/vosk/models/vosk-model-pt-0.3.zip', 
            'size': '1.2GB',
            'description': 'Portuguese large model (slower, best quality)'
        }
    },
    'en': {
        'small': {
            'url': 'https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip',
            'size': '40MB', 
            'description': 'English small model (fastest, moderate quality)'
        },
        'large': {
            'url': 'https://alphacephei.com/vosk/models/vosk-model-en-us-0.22.zip',
            'size': '1.8GB',
            'description': 'English large model (slower, best quality)'
        }
    }
}

# Default model configuration for automated installation
DEFAULT_MODEL = {
    'language': 'pt',
    'size': 'small',
    'url': 'https://alphacephei.com/vosk/models/vosk-model-small-pt-0.3.zip'
}

class VoskModelInstaller:
    """Vosk model download and installation manager"""
    
    def __init__(self, models_dir: str = None):
        """Initialize installer with models directory"""
        if models_dir is None:
            # Default to models directory in project root
            project_root = Path(__file__).parent.parent
            self.models_dir = project_root / "models" / "vosk"
        else:
            self.models_dir = Path(models_dir)
        
        # Ensure models directory exists
        self.models_dir.mkdir(parents=True, exist_ok=True)
        log.info(f"Vosk models directory: {self.models_dir}")
    
    def list_available_models(self):
        """List all available models"""
        print("\n🎯 Available Vosk Models:")
        print("=" * 60)
        
        for lang, models in VOSK_MODELS.items():
            print(f"\n📍 Language: {lang.upper()}")
            for size, info in models.items():
                print(f"   {size}: {info['description']} - {info['size']}")
    
    def download_file(self, url: str, destination: Path, description: str = "") -> bool:
        """Download file with progress indication"""
        try:
            print(f"\n⬇️  Downloading {description}...")
            print(f"    URL: {url}")
            print(f"    Destination: {destination}")
            
            response = requests.get(url, stream=True)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            downloaded_size = 0
            
            with open(destination, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded_size += len(chunk)
                        
                        # Show progress every 10MB
                        if downloaded_size % (10 * 1024 * 1024) == 0 or downloaded_size == total_size:
                            if total_size > 0:
                                progress = (downloaded_size / total_size) * 100
                                print(f"    Progress: {progress:.1f}% ({downloaded_size // (1024*1024)}MB)")
            
            print(f"✅ Download completed: {destination}")
            return True
            
        except Exception as e:
            print(f"❌ Download failed: {e}")
            if destination.exists():
                destination.unlink()  # Remove incomplete file
            return False
    
    def extract_model(self, zip_path: Path, extract_to: Path) -> Path:
        """Extract Vosk model from ZIP file"""
        try:
            print(f"\n📦 Extracting model...")
            print(f"    From: {zip_path}")
            print(f"    To: {extract_to}")
            
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(extract_to)
            
            # Find the extracted model directory
            # Vosk models typically extract to a directory like "vosk-model-small-pt-0.3"
            extracted_dirs = [d for d in extract_to.iterdir() if d.is_dir() and d.name.startswith('vosk-model')]
            
            if not extracted_dirs:
                raise Exception("No vosk-model directory found in extracted files")
            
            model_dir = extracted_dirs[0]
            print(f"✅ Model extracted to: {model_dir}")
            
            # Verify model structure (Vosk models have final.mdl in root, not am/ subdirectory)
            if not (model_dir / "final.mdl").exists():
                raise Exception("Invalid model structure - missing final.mdl file")
            
            return model_dir
            
        except Exception as e:
            print(f"❌ Extraction failed: {e}")
            raise
    
    def install_model(self, language: str = 'pt', size: str = 'small') -> Path:
        """Install a specific Vosk model"""
        if language not in VOSK_MODELS:
            raise ValueError(f"Unsupported language: {language}")
        
        if size not in VOSK_MODELS[language]:
            raise ValueError(f"Unsupported size for {language}: {size}")
        
        model_info = VOSK_MODELS[language][size]
        model_name = f"vosk-model-{size}-{language}"
        
        print(f"\n🚀 Installing Vosk Model: {model_name}")
        print(f"    Description: {model_info['description']}")
        print(f"    Size: {model_info['size']}")
        
        # Check if model already exists
        existing_models = list(self.models_dir.glob(f"*{language}*{size}*"))
        if existing_models:
            existing_model = existing_models[0]
            print(f"📋 Model already exists: {existing_model}")
            return existing_model
        
        # Download model
        zip_filename = f"{model_name}.zip"
        zip_path = self.models_dir / zip_filename
        
        if not self.download_file(model_info['url'], zip_path, model_name):
            raise Exception("Failed to download model")
        
        try:
            # Extract model
            model_dir = self.extract_model(zip_path, self.models_dir)
            
            # Clean up ZIP file
            zip_path.unlink()
            print(f"🗑️  Cleaned up: {zip_filename}")
            
            print(f"\n✅ Vosk model installed successfully!")
            print(f"    Model path: {model_dir}")
            
            return model_dir
            
        except Exception as e:
            # Clean up on failure
            if zip_path.exists():
                zip_path.unlink()
            raise e
    
    def list_installed_models(self) -> list:
        """List all installed Vosk models"""
        if not self.models_dir.exists():
            return []
        
        models = []
        for item in self.models_dir.iterdir():
            if item.is_dir() and item.name.startswith('vosk-model'):
                # Check if it's a valid model (has required files)
                if (item / "final.mdl").exists():
                    models.append(item)
        
        return models
    
    def get_recommended_model(self) -> Path:
        """Get the best available model for the current system"""
        installed = self.list_installed_models()
        
        # Priority: Portuguese small > Portuguese large > English small > English large
        preferences = [
            ('pt', 'small'),
            ('pt', 'large'), 
            ('en', 'small'),
            ('en', 'large')
        ]
        
        for lang, size in preferences:
            for model_path in installed:
                model_name = model_path.name.lower()
                if lang in model_name and size in model_name:
                    return model_path
        
        return None
    
    def update_env_file(self, model_path: Path, silent: bool = False):
        """Update .env file with Vosk model path"""
        project_root = Path(__file__).parent.parent
        env_file = project_root / ".env"
        
        try:
            # Read existing .env content
            env_lines = []
            vosk_found = False
            
            if env_file.exists():
                with open(env_file, 'r') as f:
                    for line in f:
                        if line.strip().startswith('VOSK_MODEL_PATH='):
                            # Update existing line
                            env_lines.append(f"VOSK_MODEL_PATH={model_path}\n")
                            vosk_found = True
                        else:
                            env_lines.append(line)
            
            # Add new line if not found
            if not vosk_found:
                env_lines.append(f"\n# Vosk offline transcription model\n")
                env_lines.append(f"VOSK_MODEL_PATH={model_path}\n")
            
            # Write updated content
            with open(env_file, 'w') as f:
                f.writelines(env_lines)
            
            if not silent:
                print(f"\n✅ Updated .env file:")
                print(f"    VOSK_MODEL_PATH={model_path}")
            
            return True
            
        except Exception as e:
            if not silent:
                print(f"⚠️  Failed to update .env file: {e}")
                print(f"    Please manually add: VOSK_MODEL_PATH={model_path}")
            return False
    
    def install_default_model_silent(self) -> Path:
        """
        Install default Portuguese model silently (for automated installation)
        Returns the path to the installed model or raises exception on failure
        """
        try:
            # Check if a suitable model already exists
            existing_models = self.list_installed_models()
            for model_path in existing_models:
                model_name = model_path.name.lower()
                if 'pt' in model_name and ('small' in model_name or 'vosk-model-pt' in model_name):
                    log.info(f"Vosk Portuguese model already installed: {model_path}")
                    return model_path
            
            # Install default Portuguese model
            log.info("Installing default Vosk Portuguese model...")
            model_path = self.install_model('pt', 'small')
            log.info(f"Vosk model installed successfully: {model_path}")
            return model_path
            
        except Exception as e:
            log.error(f"Failed to install default Vosk model: {e}")
            raise
    
    def setup_for_automated_installation(self) -> bool:
        """
        Setup Vosk model for automated installation (called by install scripts)
        Returns True if successful, False otherwise
        """
        try:
            # Install default model
            model_path = self.install_default_model_silent()
            
            # Update .env file
            if self.update_env_file(model_path, silent=True):
                log.info(f"Vosk setup completed: {model_path}")
                return True
            else:
                log.warning("Vosk model installed but .env update failed")
                return False
                
        except Exception as e:
            log.error(f"Automated Vosk setup failed: {e}")
            return False


def setup_vosk_automated():
    """
    Automated Vosk setup for installation scripts
    Returns True if successful, False otherwise
    """
    try:
        installer = VoskModelInstaller()
        return installer.setup_for_automated_installation()
    except Exception as e:
        log.error(f"Automated Vosk setup failed: {e}")
        return False


def main():
    """Main setup function"""
    # Check for automated mode
    if len(sys.argv) > 1 and sys.argv[1] == '--auto':
        # Automated installation mode
        print("🤖 Automated Vosk Model Installation")
        try:
            installer = VoskModelInstaller()
            model_path = installer.install_default_model_silent()
            installer.update_env_file(model_path)
            print(f"✅ Vosk model installed: {model_path}")
            return 0
        except Exception as e:
            print(f"❌ Automated installation failed: {e}")
            return 1
    
    # Interactive mode
    print("🎤 Vosk Model Setup for WhisperSilent")
    print("=" * 50)
    
    installer = VoskModelInstaller()
    
    # Show available models
    installer.list_available_models()
    
    # Show installed models
    installed = installer.list_installed_models()
    if installed:
        print(f"\n📦 Installed Models:")
        for model in installed:
            print(f"   ✅ {model.name} ({model})")
    else:
        print(f"\n📦 No models installed yet")
    
    # Interactive installation
    print(f"\n🤖 Recommended: Portuguese Small Model (fastest setup)")
    choice = input("Install Portuguese small model? [Y/n]: ").strip().lower()
    
    if choice in ['', 'y', 'yes']:
        try:
            # Install Portuguese small model
            model_path = installer.install_model('pt', 'small')
            
            # Update .env file
            installer.update_env_file(model_path)
            
            print(f"\n🎯 Setup Complete!")
            print(f"   Model: {model_path}")
            print(f"   The system is now configured for offline transcription")
            print(f"   You can test it by setting: SPEECH_RECOGNITION_ENGINE=vosk")
            
        except Exception as e:
            print(f"\n❌ Setup failed: {e}")
            return 1
    else:
        print(f"\n📋 Manual Installation:")
        print(f"   1. Download a model from: https://alphacephei.com/vosk/models")
        print(f"   2. Extract to: {installer.models_dir}")
        print(f"   3. Set VOSK_MODEL_PATH in .env file")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())