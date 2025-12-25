#!/usr/bin/env python3
"""
Setup script for Instagram Content Analyzer.
"""

import subprocess
import sys
import os
from pathlib import Path


def run_command(command, description):
    """Run a shell command and handle errors."""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e.stderr}")
        return None


def main():
    """Main setup function."""
    print("🚀 Setting up Instagram Content Analyzer...")
    
    # Check Python version
    if sys.version_info < (3, 9):
        print("❌ Python 3.9 or higher is required")
        sys.exit(1)
    
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro} detected")
    
    # Create virtual environment
    venv_path = Path("instagram_analyzer_env")
    if not venv_path.exists():
        run_command(f"{sys.executable} -m venv instagram_analyzer_env", "Creating virtual environment")
    else:
        print("✅ Virtual environment already exists")
    
    # Determine activation script path
    if os.name == 'nt':  # Windows
        activate_script = venv_path / "Scripts" / "activate"
        pip_path = venv_path / "Scripts" / "pip"
    else:  # Unix/Linux/macOS
        activate_script = venv_path / "bin" / "activate"
        pip_path = venv_path / "bin" / "pip"
    
    # Install dependencies
    run_command(f"{pip_path} install --upgrade pip", "Upgrading pip")
    run_command(f"{pip_path} install -r requirements.txt", "Installing dependencies")
    
    # Create .env file if it doesn't exist
    env_file = Path(".env")
    if not env_file.exists():
        run_command("cp .env.example .env", "Creating .env file")
        print("📝 Please edit .env file with your configuration")
    else:
        print("✅ .env file already exists")
    
    # Create temp directory
    temp_dir = Path("temp")
    if not temp_dir.exists():
        temp_dir.mkdir()
        print("✅ Created temp directory")
    
    print("\n🎉 Setup completed successfully!")
    print("\nNext steps:")
    print("1. Edit .env file with your API keys and configuration")
    print("2. Activate virtual environment:")
    if os.name == 'nt':
        print("   instagram_analyzer_env\\Scripts\\activate")
    else:
        print("   source instagram_analyzer_env/bin/activate")
    print("3. Run the application:")
    print("   uvicorn src.main:app --reload")


if __name__ == "__main__":
    main()