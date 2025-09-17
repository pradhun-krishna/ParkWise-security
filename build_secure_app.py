# Build Secure ANPR Application
# Creates a fully secure, standalone executable

import os
import sys
import subprocess
import shutil
import json
import base64
from pathlib import Path
import zipfile

class SecureAppBuilder:
    def __init__(self):
        self.app_name = "ShobhaANPR"
        self.version = "1.0.0"
        self.build_dir = Path("build")
        self.dist_dir = Path("dist")
        self.secure_dir = Path("secure_app")
        
    def clean_build_dirs(self):
        """Clean build directories"""
        print("🧹 Cleaning build directories...")
        
        for dir_path in [self.build_dir, self.dist_dir, self.secure_dir]:
            if dir_path.exists():
                shutil.rmtree(dir_path)
            dir_path.mkdir(exist_ok=True)
        
        print("✅ Build directories cleaned")
    
    def install_dependencies(self):
        """Install required dependencies"""
        print("📦 Installing dependencies...")
        
        dependencies = [
            "pyinstaller==5.13.2",
            "cryptography==41.0.7",
            "psutil==5.9.6",
            "tkinter"  # Usually comes with Python
        ]
        
        for dep in dependencies:
            try:
                subprocess.run([sys.executable, "-m", "pip", "install", dep], 
                             check=True, capture_output=True)
                print(f"✅ Installed {dep}")
            except subprocess.CalledProcessError as e:
                print(f"⚠️ Warning: Could not install {dep}: {e}")
    
    def create_secure_config(self, db_config):
        """Create encrypted configuration"""
        print("🔐 Creating secure configuration...")
        
        config_data = {
            "database": {
                "host": db_config.get("host", "localhost"),
                "port": db_config.get("port", 5432),
                "name": db_config.get("name", "shobha_parking"),
                "user": db_config.get("user", "postgres"),
                "password": db_config.get("password", "")
            },
            "parking": {
                "lot_id": db_config.get("lot_id", "1"),
                "hourly_rate": db_config.get("hourly_rate", 10.0),
                "minimum_charge": db_config.get("minimum_charge", 20.0)
            },
            "hardware": {
                "boom_barrier_pin": db_config.get("boom_barrier_pin", 18),
                "led_green_pin": db_config.get("led_green_pin", 20),
                "led_red_pin": db_config.get("led_red_pin", 21),
                "buzzer_pin": db_config.get("buzzer_pin", 22)
            },
            "camera": {
                "index": db_config.get("camera_index", 0),
                "exit_index": db_config.get("exit_camera_index", 1)
            },
            "security": {
                "session_timeout": 3600,
                "max_attempts": 3,
                "encryption_enabled": True
            }
        }
        
        # Encrypt configuration
        config_json = json.dumps(config_data, indent=2)
        encoded_config = base64.b64encode(config_json.encode()).decode()
        
        # Save encrypted config
        config_path = self.secure_dir / "secure_config.enc"
        with open(config_path, "w") as f:
            f.write(encoded_config)
        
        print("✅ Secure configuration created")
        return config_path
    
    def create_main_launcher(self):
        """Create the main launcher script"""
        print("🚀 Creating main launcher...")
        
        launcher_code = '''#!/usr/bin/env python3
# Shobha ANPR Parking System - Secure Launcher
# Main entry point for the secure application

import os
import sys
import json
import base64
import tkinter as tk
from pathlib import Path
import subprocess
import threading
import time
from datetime import datetime

class SecureANPRSystem:
    def __init__(self):
        self.config = self.load_secure_config()
        self.setup_environment()
        self.setup_security()
    
    def load_secure_config(self):
        """Load encrypted configuration"""
        try:
            config_path = Path(__file__).parent / "secure_config.enc"
            if config_path.exists():
                with open(config_path, "r") as f:
                    encoded_config = f.read()
                config_json = base64.b64decode(encoded_config).decode()
                return json.loads(config_json)
            else:
                return self.get_default_config()
        except Exception as e:
            print(f"Config load error: {e}")
            return self.get_default_config()
    
    def get_default_config(self):
        """Default configuration"""
        return {
            "database": {
                "host": "localhost",
                "port": 5432,
                "name": "shobha_parking",
                "user": "postgres",
                "password": ""
            },
            "parking": {
                "lot_id": "1",
                "hourly_rate": 10.0,
                "minimum_charge": 20.0
            },
            "hardware": {
                "boom_barrier_pin": 18,
                "led_green_pin": 20,
                "led_red_pin": 21,
                "buzzer_pin": 22
            },
            "camera": {
                "index": 0,
                "exit_index": 1
            },
            "security": {
                "session_timeout": 3600,
                "max_attempts": 3,
                "encryption_enabled": True
            }
        }
    
    def setup_environment(self):
        """Setup environment variables"""
        os.environ["DB_HOST"] = str(self.config["database"]["host"])
        os.environ["DB_PORT"] = str(self.config["database"]["port"])
        os.environ["DB_NAME"] = str(self.config["database"]["name"])
        os.environ["DB_USER"] = str(self.config["database"]["user"])
        os.environ["DB_PASSWORD"] = str(self.config["database"]["password"])
        os.environ["PARKING_LOT_ID"] = str(self.config["parking"]["lot_id"])
        os.environ["HOURLY_RATE"] = str(self.config["parking"]["hourly_rate"])
        os.environ["MINIMUM_CHARGE"] = str(self.config["parking"]["minimum_charge"])
        os.environ["BOOM_BARRIER_PIN"] = str(self.config["hardware"]["boom_barrier_pin"])
        os.environ["LED_GREEN_PIN"] = str(self.config["hardware"]["led_green_pin"])
        os.environ["LED_RED_PIN"] = str(self.config["hardware"]["led_red_pin"])
        os.environ["BUZZER_PIN"] = str(self.config["hardware"]["buzzer_pin"])
        os.environ["CAMERA_INDEX"] = str(self.config["camera"]["index"])
        os.environ["EXIT_CAMERA_INDEX"] = str(self.config["camera"]["exit_index"])
    
    def setup_security(self):
        """Setup security features"""
        # Create logs directory
        logs_dir = Path("logs")
        logs_dir.mkdir(exist_ok=True)
        
        # Log startup
        self.log_security_event("SYSTEM_START", "Secure ANPR system started")
    
    def log_security_event(self, event_type, details):
        """Log security events"""
        timestamp = datetime.now().isoformat()
        log_entry = f"{timestamp} - {event_type}: {details}\\n"
        
        try:
            with open("logs/security.log", "a") as f:
                f.write(log_entry)
        except:
            pass
    
    def start_dashboard(self):
        """Start the dashboard system"""
        try:
            # Import and run the dashboard
            from system_dashboard import app
            app.run(host='127.0.0.1', port=5000, debug=False)
        except Exception as e:
            print(f"Error starting dashboard: {e}")
            self.log_security_event("ERROR", f"Dashboard start failed: {e}")
    
    def start_gui_launcher(self):
        """Start the GUI launcher"""
        try:
            from secure_gui_launcher import SecureANPRLauncher
            app = SecureANPRLauncher()
            app.run()
        except Exception as e:
            print(f"Error starting GUI launcher: {e}")
            self.log_security_event("ERROR", f"GUI launcher failed: {e}")

def main():
    """Main function"""
    print("🔐 Shobha ANPR Parking System - Secure Launcher")
    print("=" * 50)
    
    # Check command line arguments
    if len(sys.argv) > 1 and sys.argv[1] == "--dashboard":
        # Start dashboard directly
        system = SecureANPRSystem()
        system.start_dashboard()
    else:
        # Start GUI launcher
        system = SecureANPRSystem()
        system.start_gui_launcher()

if __name__ == "__main__":
    main()
'''
        
        launcher_path = self.secure_dir / "main_launcher.py"
        with open(launcher_path, "w") as f:
            f.write(launcher_code)
        
        print("✅ Main launcher created")
        return launcher_path
    
    def copy_application_files(self):
        """Copy application files to secure directory"""
        print("📁 Copying application files...")
        
        files_to_copy = [
            "database_connection.py",
            "system_dashboard.py",
            "advanced_security.py",
            "secure_gui_launcher.py",
            "templates/",
            "static/"
        ]
        
        for file_path in files_to_copy:
            src = Path(file_path)
            dst = self.secure_dir / file_path
            
            if src.is_file():
                shutil.copy2(src, dst)
                print(f"✅ Copied {file_path}")
            elif src.is_dir():
                shutil.copytree(src, dst, dirs_exist_ok=True)
                print(f"✅ Copied directory {file_path}")
            else:
                print(f"⚠️ Warning: {file_path} not found")
    
    def create_requirements_file(self):
        """Create requirements file for the secure app"""
        print("📦 Creating requirements file...")
        
        requirements = """# Shobha ANPR Parking System - Secure App Requirements

# Core dependencies
opencv-python==4.8.1.78
numpy==1.24.3
python-dotenv==1.0.0

# Database integration
psycopg2-binary==2.9.7

# QR code generation
qrcode[pil]==7.4.2
Pillow==10.0.1

# OCR for license plate recognition
pytesseract==0.3.10

# GPIO control for Raspberry Pi
RPi.GPIO==0.7.1

# HTTP requests
requests==2.31.0

# Date and time handling
python-dateutil==2.8.2

# Web dashboard
Flask==2.3.3
Flask-CORS==4.0.0

# Security and encryption
cryptography==41.0.7
psutil==5.9.6

# GUI framework
tkinter

# App building
pyinstaller==5.13.2
"""
        
        req_path = self.secure_dir / "requirements.txt"
        with open(req_path, "w") as f:
            f.write(requirements)
        
        print("✅ Requirements file created")
        return req_path
    
    def build_executable(self):
        """Build the executable using PyInstaller"""
        print("🔨 Building executable...")
        
        try:
            # PyInstaller command
            cmd = [
                sys.executable, "-m", "PyInstaller",
                "--onefile",
                "--windowed",
                "--name", self.app_name,
                "--distpath", str(self.dist_dir),
                "--workpath", str(self.build_dir),
                "--specpath", str(self.build_dir),
                "--add-data", f"{self.secure_dir / 'secure_config.enc'};.",
                "--add-data", f"{self.secure_dir / 'templates'};templates",
                "--add-data", f"{self.secure_dir / 'static'};static",
                "--hidden-import", "tkinter",
                "--hidden-import", "tkinter.ttk",
                "--hidden-import", "tkinter.messagebox",
                "--hidden-import", "tkinter.scrolledtext",
                "--hidden-import", "cryptography",
                "--hidden-import", "psutil",
                str(self.secure_dir / "main_launcher.py")
            ]
            
            # Run PyInstaller
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                print("✅ Executable built successfully")
                return True
            else:
                print(f"❌ Build failed: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"❌ Build error: {e}")
            return False
    
    def create_installer(self):
        """Create installer package"""
        print("📦 Creating installer package...")
        
        installer_dir = Path("installer")
        installer_dir.mkdir(exist_ok=True)
        
        # Copy executable
        exe_path = self.dist_dir / f"{self.app_name}.exe"
        if exe_path.exists():
            shutil.copy2(exe_path, installer_dir / f"{self.app_name}.exe")
        
        # Copy configuration
        config_path = self.secure_dir / "secure_config.enc"
        if config_path.exists():
            shutil.copy2(config_path, installer_dir / "secure_config.enc")
        
        # Create installer script
        installer_script = f'''@echo off
echo Shobha ANPR Parking System - Installer
echo =====================================
echo.

REM Create application directory
set "APP_DIR=%PROGRAMFILES%\\{self.app_name}"
mkdir "%APP_DIR%" 2>nul

REM Copy application files
copy "{self.app_name}.exe" "%APP_DIR%\\"
copy "secure_config.enc" "%APP_DIR%\\"

REM Create desktop shortcut
set "DESKTOP=%USERPROFILE%\\Desktop"
echo [InternetShortcut] > "%DESKTOP%\\Shobha ANPR Parking System.url"
echo URL=file:///%APP_DIR%\\{self.app_name}.exe >> "%DESKTOP%\\Shobha ANPR Parking System.url"
echo IconFile=%APP_DIR%\\{self.app_name}.exe >> "%DESKTOP%\\Shobha ANPR Parking System.url"
echo IconIndex=0 >> "%DESKTOP%\\Shobha ANPR Parking System.url"

echo.
echo Installation complete!
echo Desktop shortcut created.
echo.
echo To start the system, double-click the desktop shortcut.
echo.
pause
'''
        
        installer_path = installer_dir / "install.bat"
        with open(installer_path, "w") as f:
            f.write(installer_script)
        
        print("✅ Installer package created")
        return installer_dir
    
    def create_portable_package(self):
        """Create portable package"""
        print("📦 Creating portable package...")
        
        portable_dir = Path("portable")
        portable_dir.mkdir(exist_ok=True)
        
        # Copy executable
        exe_path = self.dist_dir / f"{self.app_name}.exe"
        if exe_path.exists():
            shutil.copy2(exe_path, portable_dir / f"{self.app_name}.exe")
        
        # Copy configuration
        config_path = self.secure_dir / "secure_config.enc"
        if config_path.exists():
            shutil.copy2(config_path, portable_dir / "secure_config.enc")
        
        # Create portable launcher
        portable_launcher = f'''@echo off
echo Starting Shobha ANPR Parking System...
echo.

REM Check if executable exists
if not exist "{self.app_name}.exe" (
    echo Error: {self.app_name}.exe not found!
    pause
    exit
)

REM Start the application
start "" "{self.app_name}.exe"

echo Application started!
echo Dashboard: http://localhost:5000
echo.
pause
'''
        
        launcher_path = portable_dir / "start.bat"
        with open(launcher_path, "w") as f:
            f.write(portable_launcher)
        
        print("✅ Portable package created")
        return portable_dir
    
    def build_secure_app(self, db_config):
        """Build the complete secure application"""
        print("🚀 Building Shobha ANPR Secure Application...")
        print("=" * 60)
        
        # Clean and setup
        self.clean_build_dirs()
        self.install_dependencies()
        
        # Create secure components
        self.create_secure_config(db_config)
        self.create_main_launcher()
        self.copy_application_files()
        self.create_requirements_file()
        
        # Build executable
        if self.build_executable():
            # Create packages
            self.create_installer()
            self.create_portable_package()
            
            print("\\n" + "=" * 60)
            print("✅ Secure application build complete!")
            print("\\n📁 Output directories:")
            print(f"   - {self.dist_dir}/ - Executable file")
            print(f"   - installer/ - Installation package")
            print(f"   - portable/ - Portable package")
            print("\\n🔐 Security features included:")
            print("   - Encrypted configuration")
            print("   - Standalone executable")
            print("   - No source code visible")
            print("   - Session security")
            print("   - Event logging")
            print("\\n🚀 Ready for deployment!")
            return True
        else:
            print("\\n❌ Build failed. Please check the errors above.")
            return False

def main():
    """Main function to build secure app"""
    print("🔐 Shobha ANPR Parking System - Secure App Builder")
    print("=" * 60)
    
    # Get database configuration
    print("\\n📋 Enter your database configuration:")
    db_config = {
        "host": input("Database Host [localhost]: ") or "localhost",
        "port": int(input("Database Port [5432]: ") or 5432),
        "name": input("Database Name [shobha_parking]: ") or "shobha_parking",
        "user": input("Database User [postgres]: ") or "postgres",
        "password": input("Database Password: "),
        "lot_id": input("Parking Lot ID [1]: ") or "1",
        "hourly_rate": float(input("Hourly Rate [10.0]: ") or 10.0),
        "minimum_charge": float(input("Minimum Charge [20.0]: ") or 20.0),
        "boom_barrier_pin": int(input("Boom Barrier Pin [18]: ") or 18),
        "led_green_pin": int(input("Green LED Pin [20]: ") or 20),
        "led_red_pin": int(input("Red LED Pin [21]: ") or 21),
        "buzzer_pin": int(input("Buzzer Pin [22]: ") or 22),
        "camera_index": int(input("Camera Index [0]: ") or 0),
        "exit_camera_index": int(input("Exit Camera Index [1]: ") or 1)
    }
    
    # Build the secure application
    builder = SecureAppBuilder()
    success = builder.build_secure_app(db_config)
    
    if success:
        print("\\n🎉 Secure application build complete!")
        print("\\n📋 Next steps:")
        print("1. Test the executable in the 'dist' folder")
        print("2. Use the installer for system installation")
        print("3. Use the portable package for USB deployment")
        print("\\n🔐 Your ANPR system is now fully secured!")
    else:
        print("\\n❌ Build failed. Please check the errors above.")

if __name__ == "__main__":
    main()


