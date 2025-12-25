#!/usr/bin/env python3
"""
Validation script to verify Instagram Content Analyzer setup.
"""

import sys
import importlib
from pathlib import Path


def check_import(module_name, description):
    """Check if a module can be imported."""
    try:
        importlib.import_module(module_name)
        print(f"✅ {description}")
        return True
    except ImportError as e:
        print(f"❌ {description}: {e}")
        return False


def check_file_exists(file_path, description):
    """Check if a file exists."""
    if Path(file_path).exists():
        print(f"✅ {description}")
        return True
    else:
        print(f"❌ {description}")
        return False


def main():
    """Main validation function."""
    print("🔍 Validating Instagram Content Analyzer setup...\n")
    
    all_checks_passed = True
    
    # Check core dependencies
    print("📦 Checking core dependencies:")
    dependencies = [
        ("fastapi", "FastAPI web framework"),
        ("uvicorn", "ASGI server"),
        ("selenium", "Browser automation"),
        ("openai", "OpenAI API client"),
        ("hypothesis", "Property-based testing"),
        ("pytest", "Testing framework"),
        ("pydantic", "Data validation"),
        ("pymongo", "MongoDB driver"),
        ("cv2", "OpenCV computer vision"),
        ("requests", "HTTP client"),
    ]
    
    for module, desc in dependencies:
        if not check_import(module, desc):
            all_checks_passed = False
    
    print("\n🏗️ Checking project structure:")
    
    # Check main application files
    files_to_check = [
        ("src/main.py", "Main application file"),
        ("src/config/settings.py", "Configuration settings"),
        ("src/auth/manager.py", "Authentication manager"),
        ("src/content/retrieval.py", "Content retrieval engine"),
        ("src/analysis/multimodal.py", "Multi-modal analyzer"),
        ("src/database/content_db.py", "Content database"),
        ("src/query/processor.py", "Query processor"),
        ("src/response/generator.py", "Response generator"),
        (".env", "Environment configuration"),
        ("requirements.txt", "Python dependencies"),
        ("README.md", "Project documentation"),
    ]
    
    for file_path, desc in files_to_check:
        if not check_file_exists(file_path, desc):
            all_checks_passed = False
    
    print("\n🧪 Checking application modules:")
    
    # Check application modules
    app_modules = [
        ("src.main", "Main application"),
        ("src.config.settings", "Settings configuration"),
        ("src.models.auth", "Authentication models"),
        ("src.models.content", "Content models"),
        ("src.models.analysis", "Analysis models"),
        ("src.models.query", "Query models"),
        ("src.models.response", "Response models"),
    ]
    
    for module, desc in app_modules:
        if not check_import(module, desc):
            all_checks_passed = False
    
    print("\n🎯 Final validation:")
    
    # Test FastAPI app creation
    try:
        from src.main import app
        if app.title == "Instagram Content Analyzer":
            print("✅ FastAPI application created successfully")
        else:
            print("❌ FastAPI application configuration issue")
            all_checks_passed = False
    except Exception as e:
        print(f"❌ FastAPI application creation failed: {e}")
        all_checks_passed = False
    
    # Test settings loading
    try:
        from src.config.settings import get_settings
        settings = get_settings()
        if settings.app_name:
            print("✅ Settings configuration loaded successfully")
        else:
            print("❌ Settings configuration issue")
            all_checks_passed = False
    except Exception as e:
        print(f"❌ Settings loading failed: {e}")
        all_checks_passed = False
    
    print("\n" + "="*50)
    
    if all_checks_passed:
        print("🎉 All checks passed! Instagram Content Analyzer is ready.")
        print("\nNext steps:")
        print("1. Update .env file with your API keys")
        print("2. Start the application: uvicorn src.main:app --reload")
        print("3. Visit http://localhost:8000/docs for API documentation")
        return 0
    else:
        print("❌ Some checks failed. Please review the errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())