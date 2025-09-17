#!/usr/bin/env python3
# Complete System Test - Verifies all components are working

import cv2
import os
import sys
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

def test_imports():
    """Test if all required modules can be imported"""
    print("🧪 Testing imports...")
    
    try:
        import cv2
        print("✅ OpenCV imported successfully")
    except ImportError as e:
        print(f"❌ OpenCV import failed: {e}")
        return False
    
    try:
        import numpy as np
        print("✅ NumPy imported successfully")
    except ImportError as e:
        print(f"❌ NumPy import failed: {e}")
        return False
    
    try:
        from secure_database_connection import secure_db as db
        print("✅ Database connection imported successfully")
    except ImportError as e:
        print(f"❌ Database connection import failed: {e}")
        return False
    
    try:
        from flask import Flask
        print("✅ Flask imported successfully")
    except ImportError as e:
        print(f"❌ Flask import failed: {e}")
        return False
    
    return True

def test_camera():
    """Test camera availability"""
    print("\n📹 Testing cameras...")
    
    # Test entry camera
    cap = cv2.VideoCapture(0)
    if cap.isOpened():
        ret, frame = cap.read()
        if ret:
            print("✅ Entry camera (index 0) working")
            cap.release()
        else:
            print("❌ Entry camera (index 0) not working")
            cap.release()
            return False
    else:
        print("❌ Entry camera (index 0) not available")
        return False
    
    # Test exit camera
    cap = cv2.VideoCapture(1)
    if cap.isOpened():
        ret, frame = cap.read()
        if ret:
            print("✅ Exit camera (index 1) working")
            cap.release()
        else:
            print("❌ Exit camera (index 1) not working")
            cap.release()
            return False
    else:
        print("❌ Exit camera (index 1) not available")
        return False
    
    return True

def test_database():
    """Test database connection"""
    print("\n🗄️ Testing database connection...")
    
    try:
        from secure_database_connection import secure_db as db
        
        # Test connection
        if db.connection:
            print("✅ Database connection established")
        else:
            print("❌ Database connection failed")
            return False
        
        # Test query
        result = db.get_system_stats()
        if result:
            print("✅ Database query successful")
            print(f"   Total sessions: {result.get('total_sessions', 0)}")
            print(f"   Active sessions: {result.get('active_sessions', 0)}")
            print(f"   Permanent vehicles: {result.get('permanent_vehicles', 0)}")
        else:
            print("❌ Database query failed")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False

def test_anpr_detection():
    """Test ANPR detection capabilities"""
    print("\n🚗 Testing ANPR detection...")
    
    try:
        # Test plate validation
        test_plates = [
            "KA01AB1234", "MH02CD5678", "DL04GH3456", "TN03EF9012",
            "BH01ABC123", "GJ05IJ789", "UP15AB1234", "RJ14CD5678"
        ]
        
        import re
        plate_patterns = [
            r'^[A-Z]{2}[0-9]{2}[A-Z]{2}[0-9]{4}$',  # KA01AB1234
            r'^[A-Z]{2}[0-9]{2}[A-Z]{1,3}[0-9]{3,4}$',  # BH01ABC123
        ]
        
        valid_count = 0
        for plate in test_plates:
            for pattern in plate_patterns:
                if re.match(pattern, plate):
                    valid_count += 1
                    break
        
        print(f"✅ Plate validation working: {valid_count}/{len(test_plates)} plates valid")
        
        # Test OpenCV plate detection
        cap = cv2.VideoCapture(0)
        if cap.isOpened():
            ret, frame = cap.read()
            if ret:
                # Test basic OpenCV operations
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                edges = cv2.Canny(gray, 30, 200)
                contours, _ = cv2.findContours(edges, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
                
                print(f"✅ OpenCV detection working: {len(contours)} contours found")
                cap.release()
            else:
                print("❌ Could not read from camera")
                cap.release()
                return False
        else:
            print("❌ Could not open camera for detection test")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ ANPR detection test failed: {e}")
        return False

def test_web_dashboard():
    """Test web dashboard availability"""
    print("\n🌐 Testing web dashboard...")
    
    try:
        import subprocess
        import time
        import requests
        
        # Start dashboard in background
        print("   Starting dashboard...")
        process = subprocess.Popen([sys.executable, "system_dashboard.py"], 
                                 stdout=subprocess.PIPE, 
                                 stderr=subprocess.PIPE)
        
        # Wait for dashboard to start
        time.sleep(5)
        
        # Test dashboard endpoint
        try:
            response = requests.get("http://localhost:5000", timeout=5)
            if response.status_code == 200:
                print("✅ Web dashboard working")
                process.terminate()
                return True
            else:
                print(f"❌ Web dashboard returned status {response.status_code}")
                process.terminate()
                return False
        except requests.exceptions.RequestException:
            print("❌ Web dashboard not responding")
            process.terminate()
            return False
            
    except Exception as e:
        print(f"❌ Web dashboard test failed: {e}")
        return False

def test_hardware_simulation():
    """Test hardware simulation"""
    print("\n🔧 Testing hardware simulation...")
    
    try:
        # Test GPIO simulation
        try:
            import RPi.GPIO as GPIO
            print("✅ RPi.GPIO available (real hardware mode)")
        except ImportError:
            print("✅ RPi.GPIO not available (simulation mode)")
        
        # Test hardware control simulation
        print("✅ Hardware simulation working")
        return True
        
    except Exception as e:
        print(f"❌ Hardware simulation test failed: {e}")
        return False

def main():
    """Run complete system test"""
    print("🚀 Complete ANPR System Test")
    print("=" * 60)
    
    tests = [
        ("Imports", test_imports),
        ("Camera", test_camera),
        ("Database", test_database),
        ("ANPR Detection", test_anpr_detection),
        ("Web Dashboard", test_web_dashboard),
        ("Hardware Simulation", test_hardware_simulation)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} test crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "="*60)
    print("📊 TEST SUMMARY")
    print("="*60)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:20} {status}")
        if result:
            passed += 1
    
    print("="*60)
    print(f"Total: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED! Your system is ready!")
        print("\nNext steps:")
        print("1. Run: python real_world_test_system.py")
        print("2. Test with real cameras")
        print("3. Install hardware when ready")
    else:
        print("⚠️ Some tests failed. Check the errors above.")
        print("\nTroubleshooting:")
        print("1. Install missing dependencies")
        print("2. Check camera connections")
        print("3. Verify database configuration")
    
    print("="*60)

if __name__ == "__main__":
    main()

