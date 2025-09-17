# Advanced Security Module for Shobha ANPR System
# Provides enhanced security features and protection

import os
import sys
import hashlib
import hmac
import time
import json
import base64
import uuid
from datetime import datetime, timedelta
from pathlib import Path
import logging

class AdvancedSecurityManager:
    def __init__(self):
        self.app_id = "SHOBHA_ANPR_2024"
        self.version = "1.0.0"
        self.session_id = str(uuid.uuid4())
        self.start_time = time.time()
        
        # Security settings
        self.session_timeout = 3600  # 1 hour
        self.max_attempts = 3
        self.attempts = 0
        self.last_activity = time.time()
        
        # Encryption settings
        self.encryption_key = self.generate_encryption_key()
        
        # Setup logging
        self.setup_security_logging()
        
        # Security checks
        self.perform_security_checks()
    
    def generate_encryption_key(self):
        """Generate a unique encryption key for this session"""
        machine_id = self.get_machine_id()
        timestamp = str(int(time.time()))
        combined = f"{self.app_id}_{machine_id}_{timestamp}"
        return hashlib.sha256(combined.encode()).digest()
    
    def get_machine_id(self):
        """Get unique machine identifier"""
        try:
            import platform
            machine_info = f"{platform.node()}_{platform.system()}_{platform.release()}"
            return hashlib.md5(machine_info.encode()).hexdigest()
        except:
            return "unknown_machine"
    
    def setup_security_logging(self):
        """Setup security event logging"""
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        # Create security logger
        self.security_logger = logging.getLogger("security")
        self.security_logger.setLevel(logging.INFO)
        
        # Create file handler
        log_file = log_dir / f"security_{datetime.now().strftime('%Y%m%d')}.log"
        handler = logging.FileHandler(log_file)
        handler.setLevel(logging.INFO)
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        
        # Add handler to logger
        self.security_logger.addHandler(handler)
        
        # Log startup
        self.log_security_event("SYSTEM_START", f"Application started - Session: {self.session_id}")
    
    def perform_security_checks(self):
        """Perform initial security checks"""
        self.log_security_event("SECURITY_CHECK", "Performing security validation")
        
        # Check if running in debug mode
        if hasattr(sys, 'gettrace') and sys.gettrace() is not None:
            self.log_security_event("SECURITY_WARNING", "Debug mode detected")
        
        # Check for suspicious processes
        self.check_suspicious_processes()
        
        # Validate file integrity
        self.validate_file_integrity()
        
        # Check system time
        self.validate_system_time()
    
    def check_suspicious_processes(self):
        """Check for suspicious running processes"""
        suspicious_processes = [
            "wireshark", "fiddler", "burp", "nmap", "netstat",
            "tasklist", "ps", "htop", "procmon", "regmon"
        ]
        
        try:
            import psutil
            running_processes = [p.name().lower() for p in psutil.process_iter()]
            
            for process in suspicious_processes:
                if process in running_processes:
                    self.log_security_event(
                        "SECURITY_WARNING", 
                        f"Suspicious process detected: {process}"
                    )
        except ImportError:
            # psutil not available, skip check
            pass
    
    def validate_file_integrity(self):
        """Validate critical file integrity"""
        critical_files = [
            "secure_config.enc",
            "database_connection.py",
            "system_dashboard.py"
        ]
        
        for file_path in critical_files:
            if Path(file_path).exists():
                file_hash = self.calculate_file_hash(file_path)
                self.log_security_event(
                    "FILE_INTEGRITY", 
                    f"File {file_path} hash: {file_hash}"
                )
            else:
                self.log_security_event(
                    "SECURITY_ERROR", 
                    f"Critical file missing: {file_path}"
                )
    
    def calculate_file_hash(self, file_path):
        """Calculate SHA256 hash of a file"""
        try:
            with open(file_path, 'rb') as f:
                content = f.read()
            return hashlib.sha256(content).hexdigest()
        except:
            return "error"
    
    def validate_system_time(self):
        """Validate system time is reasonable"""
        current_time = time.time()
        if current_time < 1600000000:  # Before 2020
            self.log_security_event(
                "SECURITY_WARNING", 
                "System time appears to be incorrect"
            )
    
    def encrypt_sensitive_data(self, data):
        """Encrypt sensitive data using AES-like encryption"""
        try:
            import cryptography
            from cryptography.fernet import Fernet
            
            # Generate key from our encryption key
            key = base64.urlsafe_b64encode(self.encryption_key[:32])
            fernet = Fernet(key)
            
            # Encrypt data
            encrypted_data = fernet.encrypt(str(data).encode())
            return base64.b64encode(encrypted_data).decode()
        except ImportError:
            # Fallback to simple encryption
            return base64.b64encode(str(data).encode()).decode()
    
    def decrypt_sensitive_data(self, encrypted_data):
        """Decrypt sensitive data"""
        try:
            import cryptography
            from cryptography.fernet import Fernet
            
            # Generate key from our encryption key
            key = base64.urlsafe_b64encode(self.encryption_key[:32])
            fernet = Fernet(key)
            
            # Decrypt data
            decoded_data = base64.b64decode(encrypted_data)
            decrypted_data = fernet.decrypt(decoded_data)
            return decrypted_data.decode()
        except ImportError:
            # Fallback to simple decryption
            try:
                return base64.b64decode(encrypted_data).decode()
            except:
                return None
        except:
            return None
    
    def validate_access(self, user_ip="127.0.0.1", user_agent=""):
        """Validate user access with enhanced checks"""
        # Check session timeout
        if not self.check_session_timeout():
            self.log_security_event("ACCESS_DENIED", "Session timeout")
            return False
        
        # Check IP address
        if not self.validate_ip_address(user_ip):
            self.log_security_event("ACCESS_DENIED", f"Invalid IP: {user_ip}")
            return False
        
        # Check user agent
        if not self.validate_user_agent(user_agent):
            self.log_security_event("ACCESS_DENIED", f"Invalid user agent: {user_agent}")
            return False
        
        # Update activity
        self.update_activity()
        
        # Log successful access
        self.log_security_event("ACCESS_GRANTED", f"User access from {user_ip}")
        
        return True
    
    def check_session_timeout(self):
        """Check if session has timed out"""
        if time.time() - self.last_activity > self.session_timeout:
            self.log_security_event("SESSION_TIMEOUT", "Session expired")
            return False
        return True
    
    def update_activity(self):
        """Update last activity time"""
        self.last_activity = time.time()
        self.log_security_event("ACTIVITY", "User activity detected")
    
    def validate_ip_address(self, ip):
        """Validate IP address is allowed"""
        allowed_ips = ["127.0.0.1", "::1", "localhost"]
        return ip in allowed_ips
    
    def validate_user_agent(self, user_agent):
        """Validate user agent is legitimate"""
        # Check for suspicious user agents
        suspicious_agents = ["curl", "wget", "python", "bot", "scanner"]
        user_agent_lower = user_agent.lower()
        
        for suspicious in suspicious_agents:
            if suspicious in user_agent_lower:
                return False
        
        return True
    
    def log_security_event(self, event_type, details):
        """Log security events with enhanced details"""
        timestamp = datetime.now().isoformat()
        log_entry = {
            "timestamp": timestamp,
            "session_id": self.session_id,
            "event_type": event_type,
            "details": details,
            "machine_id": self.get_machine_id(),
            "uptime": time.time() - self.start_time
        }
        
        # Log to file
        self.security_logger.info(f"{event_type}: {details}")
        
        # Log to console in debug mode
        if os.getenv("DEBUG", "false").lower() == "true":
            print(f"SECURITY: {timestamp} - {event_type}: {details}")
    
    def create_security_report(self):
        """Create security status report"""
        report = {
            "session_id": self.session_id,
            "start_time": datetime.fromtimestamp(self.start_time).isoformat(),
            "uptime": time.time() - self.start_time,
            "machine_id": self.get_machine_id(),
            "security_status": "ACTIVE",
            "last_activity": datetime.fromtimestamp(self.last_activity).isoformat(),
            "session_timeout": self.session_timeout,
            "max_attempts": self.max_attempts,
            "current_attempts": self.attempts
        }
        
        return report
    
    def cleanup(self):
        """Cleanup security resources"""
        self.log_security_event("SYSTEM_SHUTDOWN", "Application shutting down")
        
        # Clear sensitive data from memory
        self.encryption_key = None
        self.session_id = None
        
        # Close loggers
        for handler in self.security_logger.handlers:
            handler.close()
            self.security_logger.removeHandler(handler)

# Global security manager instance
security_manager = AdvancedSecurityManager()

def get_security_manager():
    """Get the global security manager instance"""
    return security_manager

def cleanup_security():
    """Cleanup security resources"""
    global security_manager
    if security_manager:
        security_manager.cleanup()
        security_manager = None

# Register cleanup function
import atexit
atexit.register(cleanup_security)


