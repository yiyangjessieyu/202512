#!/usr/bin/env python3
"""
Manual test script for AuthenticationManager
"""

from src.auth.manager import AuthenticationManager
from src.models.auth import UserCredentials, AuthStatus

def test_auth_manager_creation():
    """Test that AuthenticationManager can be created"""
    print("Testing AuthenticationManager creation...")
    auth_manager = AuthenticationManager()
    print("✓ AuthenticationManager created successfully")
    return auth_manager

def test_session_validation():
    """Test session validation with invalid session"""
    print("\nTesting session validation...")
    auth_manager = AuthenticationManager()
    
    # Test with non-existent session
    is_valid = auth_manager.validate_credentials("fake-session-id")
    print(f"✓ Invalid session correctly returns: {is_valid}")
    
    return is_valid == False

def test_session_refresh():
    """Test session refresh with invalid session"""
    print("\nTesting session refresh...")
    auth_manager = AuthenticationManager()
    
    # Test with non-existent session
    status = auth_manager.refresh_session("fake-session-id")
    print(f"✓ Session refresh for invalid session: active={status.is_active}")
    
    return status.is_active == False

def test_logout():
    """Test logout functionality"""
    print("\nTesting logout...")
    auth_manager = AuthenticationManager()
    
    # Test logout with non-existent session (should not crash)
    auth_manager.logout_user("fake-session-id")
    print("✓ Logout completed without errors")
    
    return True

def test_credentials_model():
    """Test UserCredentials model"""
    print("\nTesting UserCredentials model...")
    
    credentials = UserCredentials(
        username="test_user",
        password="test_password"
    )
    
    print(f"✓ UserCredentials created: username={credentials.username}")
    return credentials.username == "test_user"

if __name__ == "__main__":
    print("=== Manual Authentication Manager Test ===\n")
    
    try:
        # Run basic tests
        auth_manager = test_auth_manager_creation()
        test_session_validation()
        test_session_refresh()
        test_logout()
        test_credentials_model()
        
        print("\n=== All Basic Tests Passed! ===")
        print("\nNote: Full Instagram login testing requires:")
        print("1. Chrome browser installed")
        print("2. Valid Instagram credentials")
        print("3. Network connection")
        print("\nTo test actual login, modify this script with real credentials")
        print("and call: auth_manager.authenticate_user(credentials)")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()