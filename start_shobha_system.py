#!/usr/bin/env python3
"""
Shobha Apartment ANPR System Startup
Easy way to start the Shobha-specific system
"""

import sys
import os
import time
from shobha_anpr_dashboard import main

def check_requirements():
    """Check if all requirements are met"""
    print("🔍 Checking System Requirements...")
    print("=" * 50)
    
    # Check OpenCV
    try:
        import cv2
        print("✅ OpenCV installed")
    except ImportError:
        print("❌ OpenCV not installed")
        print("💡 Install with: pip install opencv-python")
        return False
    
    # Check Flask
    try:
        import flask
        print("✅ Flask installed")
    except ImportError:
        print("❌ Flask not installed")
        print("💡 Install with: pip install flask")
        return False
    
    # Check camera
    try:
        cap = cv2.VideoCapture(0)
        if cap.isOpened():
            print("✅ Camera detected")
            cap.release()
        else:
            print("⚠️ Camera not detected - system will run in demo mode")
    except Exception as e:
        print(f"⚠️ Camera check failed: {e}")
    
    # Check database (optional)
    try:
        from secure_database_connection import secure_db
        print("✅ Database connection available")
    except ImportError:
        print("⚠️ Database not available - running in demo mode")
    
    print("=" * 50)
    return True

def main_startup():
    """Main startup function"""
    print("🏠 Shobha Apartment ANPR System")
    print("=" * 50)
    print("Features:")
    print("• Live camera feed in dashboard")
    print("• Real-time license plate detection")
    print("• Shobha database integration")
    print("• Automatic boom barrier control")
    print("• Detected plates list")
    print("=" * 50)
    
    # Check requirements
    if not check_requirements():
        print("❌ Requirements not met. Please install missing dependencies.")
        sys.exit(1)
    
    print("🚀 Starting Shobha ANPR System...")
    print("🌐 Dashboard will be available at: http://localhost:5000")
    print("📹 Live camera feed: http://localhost:5000/api/live_feed")
    print("=" * 50)
    print("Press Ctrl+C to stop the system")
    print("=" * 50)
    
    try:
        # Start the system
        main()
    except KeyboardInterrupt:
        print("\n🛑 Shobha ANPR System stopped by user")
    except Exception as e:
        print(f"❌ Error starting system: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main_startup()
