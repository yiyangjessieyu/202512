"""
Authentication Manager for Instagram login and session management.
"""

import json
import time
import uuid
import logging
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException

from src.models.auth import UserCredentials, AuthResult, SessionStatus, AuthStatus


class AuthenticationManager:
    """Manages Instagram authentication and session persistence."""
    
    def __init__(self, session_storage_path: str = "sessions"):
        """
        Initialize the authentication manager.
        
        Args:
            session_storage_path: Path to store session data
        """
        self.active_sessions: Dict[str, Dict[str, Any]] = {}
        self.session_storage_path = Path(session_storage_path)
        self.session_storage_path.mkdir(exist_ok=True)
        self.logger = logging.getLogger(__name__)
        
        # Load existing sessions
        self._load_sessions()
    
    def authenticate_user(self, credentials: UserCredentials) -> AuthResult:
        """
        Initiates Instagram login flow using browser automation.
        
        Args:
            credentials: User login credentials
            
        Returns:
            AuthResult with success status and session info
        """
        try:
            # Set up Chrome options for automation
            chrome_options = Options()
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            # Create webdriver instance
            driver = webdriver.Chrome(options=chrome_options)
            driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            try:
                # Navigate to Instagram login page
                driver.get("https://www.instagram.com/accounts/login/")
                
                # Wait for page to load
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.NAME, "username"))
                )
                
                # Add human-like delay
                time.sleep(2)
                
                # Find and fill username field
                username_field = driver.find_element(By.NAME, "username")
                username_field.clear()
                username_field.send_keys(credentials.username)
                
                # Add delay between fields
                time.sleep(1)
                
                # Find and fill password field
                password_field = driver.find_element(By.NAME, "password")
                password_field.clear()
                password_field.send_keys(credentials.password)
                
                # Add delay before clicking login
                time.sleep(1)
                
                # Click login button
                login_button = driver.find_element(By.XPATH, "//button[@type='submit']")
                login_button.click()
                
                # Wait for login to process
                time.sleep(5)
                
                # Check for successful login by looking for home page elements
                try:
                    # Look for elements that indicate successful login
                    WebDriverWait(driver, 10).until(
                        lambda d: d.current_url.startswith("https://www.instagram.com/") and 
                                 not d.current_url.endswith("/accounts/login/")
                    )
                    
                    # Check for error messages
                    error_elements = driver.find_elements(By.XPATH, "//*[contains(text(), 'incorrect') or contains(text(), 'error') or contains(text(), 'Sorry')]")
                    if error_elements:
                        return AuthResult(
                            status=AuthStatus.FAILED,
                            message="Invalid credentials provided"
                        )
                    
                    # Extract session cookies for persistence
                    cookies = driver.get_cookies()
                    session_id = str(uuid.uuid4())
                    expires_at = datetime.now() + timedelta(hours=24)
                    
                    # Store session data
                    session_data = {
                        "session_id": session_id,
                        "username": credentials.username,
                        "cookies": cookies,
                        "expires_at": expires_at.isoformat(),
                        "last_activity": datetime.now().isoformat(),
                        "user_agent": driver.execute_script("return navigator.userAgent;")
                    }
                    
                    self.active_sessions[session_id] = session_data
                    self._save_session(session_id, session_data)
                    
                    self.logger.info(f"Successfully authenticated user: {credentials.username}")
                    
                    return AuthResult(
                        status=AuthStatus.SUCCESS,
                        session_id=session_id,
                        expires_at=expires_at,
                        message="Authentication successful"
                    )
                    
                except TimeoutException:
                    # Check if we're still on login page (failed login)
                    if "login" in driver.current_url:
                        return AuthResult(
                            status=AuthStatus.FAILED,
                            message="Login failed - please check credentials"
                        )
                    else:
                        # Might be a captcha or 2FA challenge
                        return AuthResult(
                            status=AuthStatus.FAILED,
                            message="Login requires additional verification (captcha/2FA)"
                        )
                        
            finally:
                driver.quit()
                
        except WebDriverException as e:
            self.logger.error(f"WebDriver error during authentication: {str(e)}")
            return AuthResult(
                status=AuthStatus.FAILED,
                message="Browser automation failed - please try again"
            )
        except Exception as e:
            self.logger.error(f"Unexpected error during authentication: {str(e)}")
            return AuthResult(
                status=AuthStatus.FAILED,
                message="Authentication failed due to unexpected error"
            )
    
    def refresh_session(self, session_id: str) -> SessionStatus:
        """
        Maintains active session by checking validity and updating activity.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Current session status
        """
        if session_id not in self.active_sessions:
            return SessionStatus(
                session_id=session_id,
                is_active=False,
                expires_at=datetime.now(),
                last_activity=datetime.now()
            )
        
        session_data = self.active_sessions[session_id]
        expires_at = datetime.fromisoformat(session_data["expires_at"])
        
        # Check if session has expired
        if datetime.now() > expires_at:
            self._remove_session(session_id)
            return SessionStatus(
                session_id=session_id,
                is_active=False,
                expires_at=expires_at,
                last_activity=datetime.fromisoformat(session_data["last_activity"])
            )
        
        # Update last activity
        session_data["last_activity"] = datetime.now().isoformat()
        self.active_sessions[session_id] = session_data
        self._save_session(session_id, session_data)
        
        return SessionStatus(
            session_id=session_id,
            is_active=True,
            expires_at=expires_at,
            last_activity=datetime.now()
        )
    
    def validate_credentials(self, session_id: str) -> bool:
        """
        Checks authentication status by validating session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            True if session is valid, False otherwise
        """
        if session_id not in self.active_sessions:
            return False
        
        session_data = self.active_sessions[session_id]
        expires_at = datetime.fromisoformat(session_data["expires_at"])
        
        # Check if session has expired
        if datetime.now() > expires_at:
            self._remove_session(session_id)
            return False
        
        return True
    
    def logout_user(self, session_id: str) -> None:
        """
        Logs out user and cleans up session data.
        
        Args:
            session_id: Session identifier
        """
        if session_id in self.active_sessions:
            username = self.active_sessions[session_id].get("username", "unknown")
            self._remove_session(session_id)
            self.logger.info(f"User logged out: {username}")
    
    def get_session_cookies(self, session_id: str) -> Optional[list]:
        """
        Retrieves session cookies for authenticated requests.
        
        Args:
            session_id: Session identifier
            
        Returns:
            List of cookies if session is valid, None otherwise
        """
        if not self.validate_credentials(session_id):
            return None
        
        return self.active_sessions[session_id].get("cookies")
    
    def get_session_user_agent(self, session_id: str) -> Optional[str]:
        """
        Retrieves user agent for the session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            User agent string if session is valid, None otherwise
        """
        if not self.validate_credentials(session_id):
            return None
        
        return self.active_sessions[session_id].get("user_agent")
    
    def _load_sessions(self) -> None:
        """Load existing sessions from storage."""
        try:
            for session_file in self.session_storage_path.glob("*.json"):
                with open(session_file, 'r') as f:
                    session_data = json.load(f)
                    session_id = session_data["session_id"]
                    
                    # Check if session is still valid
                    expires_at = datetime.fromisoformat(session_data["expires_at"])
                    if datetime.now() < expires_at:
                        self.active_sessions[session_id] = session_data
                    else:
                        # Remove expired session file
                        session_file.unlink()
        except Exception as e:
            self.logger.error(f"Error loading sessions: {str(e)}")
    
    def _save_session(self, session_id: str, session_data: Dict[str, Any]) -> None:
        """Save session data to storage."""
        try:
            session_file = self.session_storage_path / f"{session_id}.json"
            with open(session_file, 'w') as f:
                json.dump(session_data, f, indent=2)
        except Exception as e:
            self.logger.error(f"Error saving session {session_id}: {str(e)}")
    
    def _remove_session(self, session_id: str) -> None:
        """Remove session from memory and storage."""
        try:
            # Remove from active sessions
            if session_id in self.active_sessions:
                del self.active_sessions[session_id]
            
            # Remove session file
            session_file = self.session_storage_path / f"{session_id}.json"
            if session_file.exists():
                session_file.unlink()
        except Exception as e:
            self.logger.error(f"Error removing session {session_id}: {str(e)}")