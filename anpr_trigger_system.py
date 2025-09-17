#!/usr/bin/env python3
# ANPR Trigger System - Complete Entry/Exit Control
# Handles camera triggers, plate detection, database checking, and boom barrier control

import cv2
import numpy as np
import re
import time
import threading
from datetime import datetime
import os
from dotenv import load_dotenv
from secure_database_connection import secure_db as db

load_dotenv()

class ANPRTriggerSystem:
    def __init__(self):
        # Camera configuration
        self.entry_camera_index = int(os.getenv('ENTRY_CAMERA_INDEX', 0))
        self.exit_camera_index = int(os.getenv('EXIT_CAMERA_INDEX', 1))
        
        # GPIO configuration (for Raspberry Pi)
        self.entry_barrier_pin = int(os.getenv('ENTRY_BARRIER_PIN', 18))
        self.exit_barrier_pin = int(os.getenv('EXIT_BARRIER_PIN', 19))
        self.entry_led_pin = int(os.getenv('ENTRY_LED_PIN', 20))
        self.exit_led_pin = int(os.getenv('EXIT_LED_PIN', 21))
        self.buzzer_pin = int(os.getenv('BUZZER_PIN', 22))
        
        # Detection settings
        self.detection_confidence = 0.7
        self.plate_detection_interval = 2  # seconds
        self.barrier_open_time = 15  # seconds
        
        # System state
        self.entry_camera_active = False
        self.exit_camera_active = False
        self.entry_barrier_open = False
        self.exit_barrier_open = False
        
        # Threading
        self.entry_thread = None
        self.exit_thread = None
        self.running = False
        
        # Setup GPIO (simulation mode on Windows)
        self.setup_gpio()
        
        # Indian license plate patterns
        self.plate_patterns = [
            r'^[A-Z]{2}[0-9]{2}[A-Z]{2}[0-9]{4}$',  # KA01AB1234
            r'^[A-Z]{2}[0-9]{2}[A-Z]{1,3}[0-9]{3,4}$',  # BH01ABC123
        ]
        
        print("🚗 ANPR Trigger System Initialized")
        print(f"   Entry Camera: {self.entry_camera_index}")
        print(f"   Exit Camera: {self.exit_camera_index}")
        print(f"   Entry Barrier Pin: {self.entry_barrier_pin}")
        print(f"   Exit Barrier Pin: {self.exit_barrier_pin}")
    
    def setup_gpio(self):
        """Setup GPIO pins (simulation mode on Windows)"""
        try:
            import RPi.GPIO as GPIO
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(self.entry_barrier_pin, GPIO.OUT)
            GPIO.setup(self.exit_barrier_pin, GPIO.OUT)
            GPIO.setup(self.entry_led_pin, GPIO.OUT)
            GPIO.setup(self.exit_led_pin, GPIO.OUT)
            GPIO.setup(self.buzzer_pin, GPIO.OUT)
            print("✅ GPIO initialized (Raspberry Pi mode)")
        except ImportError:
            print("⚠️ GPIO not available - running in simulation mode")
            self.gpio_available = False
    
    def detect_license_plates(self, frame):
        """Detect license plates in frame using OpenCV"""
        # Convert to grayscale
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Apply bilateral filter
        filtered = cv2.bilateralFilter(gray, 11, 17, 17)
        
        # Edge detection
        edges = cv2.Canny(filtered, 30, 200)
        
        # Find contours
        contours, _ = cv2.findContours(edges, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        
        # Sort contours by area
        contours = sorted(contours, key=cv2.contourArea, reverse=True)[:5]
        
        plates = []
        
        for contour in contours:
            # Approximate contour
            approx = cv2.approxPolyDP(contour, 0.02 * cv2.arcLength(contour, True), True)
            
            # Check if contour is rectangular
            if len(approx) == 4:
                x, y, w, h = cv2.boundingRect(contour)
                
                # Check aspect ratio (license plates are typically wider than tall)
                aspect_ratio = w / h
                if 2.0 <= aspect_ratio <= 5.0 and w > 100 and h > 30:
                    # Extract license plate region
                    plate_region = frame[y:y+h, x:x+w]
                    plates.append({
                        'region': plate_region,
                        'coordinates': (x, y, w, h),
                        'confidence': 0.8  # Simulated confidence
                    })
        
        return plates
    
    def extract_plate_text(self, plate_image):
        """Extract text from license plate image"""
        try:
            # Convert to grayscale
            gray = cv2.cvtColor(plate_image, cv2.COLOR_BGR2GRAY)
            
            # Apply threshold
            _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            
            # Use Tesseract if available
            try:
                import pytesseract
                custom_config = r'--oem 3 --psm 8 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
                text = pytesseract.image_to_string(thresh, config=custom_config)
                text = re.sub(r'[^A-Z0-9]', '', text.upper())
                return text
            except ImportError:
                # Simulate OCR for testing
                return self.simulate_ocr(plate_image)
                
        except Exception as e:
            print(f"❌ OCR Error: {e}")
            return ""
    
    def simulate_ocr(self, plate_image):
        """Simulate OCR for testing purposes"""
        # This is a simulation - in real implementation, use Tesseract
        simulated_plates = [
            "KA01AB1234", "MH02CD5678", "DL04GH3456", "TN03EF9012",
            "BH01ABC123", "GJ05IJ789", "UP15AB1234", "RJ14CD5678"
        ]
        
        # Return a random plate for testing
        import random
        return random.choice(simulated_plates)
    
    def validate_indian_plate(self, text):
        """Validate Indian license plate format"""
        if not text or len(text) < 8:
            return False
        
        # Clean text
        text = re.sub(r'[^A-Z0-9]', '', text.upper())
        
        # Check patterns
        for pattern in self.plate_patterns:
            if re.match(pattern, text):
                return True
        
        return False
    
    def check_permanent_parking(self, plate_number):
        """Check if vehicle is in permanent parking database"""
        try:
            query = "SELECT * FROM shobha_permanent_parking WHERE vehicle_number = %s"
            result = db.execute_query(query, (plate_number,), fetch_one=True)
            return result is not None
        except Exception as e:
            print(f"❌ Database error: {e}")
            return False
    
    def create_entry_session(self, plate_number):
        """Create entry session in database"""
        try:
            # Check if already in permanent parking
            if self.check_permanent_parking(plate_number):
                print(f"✅ Permanent vehicle {plate_number} - Auto entry")
                return True
            
            # Create new session
            query = """
                INSERT INTO shobha_permanent_parking_sessions 
                (permanent_parking_id, entry_time) 
                VALUES ((SELECT id FROM shobha_permanent_parking WHERE vehicle_number = %s), %s)
            """
            result = db.execute_query(query, (plate_number, datetime.now()))
            print(f"✅ Entry session created for {plate_number}")
            return True
            
        except Exception as e:
            print(f"❌ Error creating entry session: {e}")
            return False
    
    def create_exit_session(self, plate_number):
        """Create exit session in database"""
        try:
            # Update session with exit time
            query = """
                UPDATE shobha_permanent_parking_sessions 
                SET exit_time = %s, duration_minutes = EXTRACT(EPOCH FROM (%s - entry_time))/60
                WHERE permanent_parking_id = (SELECT id FROM shobha_permanent_parking WHERE vehicle_number = %s)
                AND exit_time IS NULL
            """
            result = db.execute_query(query, (datetime.now(), datetime.now(), plate_number))
            print(f"✅ Exit session created for {plate_number}")
            return True
            
        except Exception as e:
            print(f"❌ Error creating exit session: {e}")
            return False
    
    def control_barrier(self, barrier_pin, action, led_pin=None):
        """Control boom barrier"""
        try:
            if action == "open":
                print(f"🚧 Opening barrier on pin {barrier_pin}")
                # GPIO.output(barrier_pin, GPIO.HIGH)  # Uncomment for real hardware
                if led_pin:
                    # GPIO.output(led_pin, GPIO.HIGH)  # Green LED
                    print(f"🟢 LED on pin {led_pin} - GREEN")
                return True
            elif action == "close":
                print(f"🚧 Closing barrier on pin {barrier_pin}")
                # GPIO.output(barrier_pin, GPIO.LOW)  # Uncomment for real hardware
                if led_pin:
                    # GPIO.output(led_pin, GPIO.LOW)  # LED off
                    print(f"🔴 LED on pin {led_pin} - OFF")
                return True
        except Exception as e:
            print(f"❌ Barrier control error: {e}")
            return False
    
    def trigger_buzzer(self, duration=1):
        """Trigger buzzer"""
        try:
            print(f"🔊 Buzzer triggered for {duration} seconds")
            # GPIO.output(self.buzzer_pin, GPIO.HIGH)  # Uncomment for real hardware
            time.sleep(duration)
            # GPIO.output(self.buzzer_pin, GPIO.LOW)  # Uncomment for real hardware
        except Exception as e:
            print(f"❌ Buzzer error: {e}")
    
    def process_entry_camera(self):
        """Process entry camera feed"""
        print("📹 Starting entry camera processing...")
        
        cap = cv2.VideoCapture(self.entry_camera_index)
        if not cap.isOpened():
            print(f"❌ Could not open entry camera {self.entry_camera_index}")
            return
        
        frame_count = 0
        last_detection_time = 0
        
        while self.running:
            ret, frame = cap.read()
            if not ret:
                continue
            
            frame_count += 1
            current_time = time.time()
            
            # Process every 30th frame to reduce CPU load
            if frame_count % 30 == 0 and (current_time - last_detection_time) > self.plate_detection_interval:
                # Detect license plates
                plates = self.detect_license_plates(frame)
                
                for plate in plates:
                    # Extract text
                    plate_text = self.extract_plate_text(plate['region'])
                    
                    if plate_text and self.validate_indian_plate(plate_text):
                        print(f"🚗 Entry detected: {plate_text}")
                        
                        # Check database
                        if self.check_permanent_parking(plate_text):
                            print(f"✅ Permanent vehicle {plate_text} - Opening barrier")
                            
                            # Open entry barrier
                            self.control_barrier(self.entry_barrier_pin, "open", self.entry_led_pin)
                            self.entry_barrier_open = True
                            
                            # Create entry session
                            self.create_entry_session(plate_text)
                            
                            # Trigger buzzer
                            self.trigger_buzzer(2)
                            
                            # Close barrier after delay
                            threading.Timer(self.barrier_open_time, self.close_entry_barrier).start()
                            
                            last_detection_time = current_time
                            break
                        else:
                            print(f"❌ Vehicle {plate_text} not in permanent parking")
                            # Trigger buzzer for unauthorized vehicle
                            self.trigger_buzzer(1)
            
            # Display frame (optional)
            cv2.imshow('Entry Camera - ANPR System', frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        
        cap.release()
        cv2.destroyAllWindows()
        print("📹 Entry camera processing stopped")
    
    def process_exit_camera(self):
        """Process exit camera feed"""
        print("📹 Starting exit camera processing...")
        
        cap = cv2.VideoCapture(self.exit_camera_index)
        if not cap.isOpened():
            print(f"❌ Could not open exit camera {self.exit_camera_index}")
            return
        
        frame_count = 0
        last_detection_time = 0
        
        while self.running:
            ret, frame = cap.read()
            if not ret:
                continue
            
            frame_count += 1
            current_time = time.time()
            
            # Process every 30th frame to reduce CPU load
            if frame_count % 30 == 0 and (current_time - last_detection_time) > self.plate_detection_interval:
                # Detect license plates
                plates = self.detect_license_plates(frame)
                
                for plate in plates:
                    # Extract text
                    plate_text = self.extract_plate_text(plate['region'])
                    
                    if plate_text and self.validate_indian_plate(plate_text):
                        print(f"🚗 Exit detected: {plate_text}")
                        
                        # Check database
                        if self.check_permanent_parking(plate_text):
                            print(f"✅ Permanent vehicle {plate_text} - Opening barrier")
                            
                            # Open exit barrier
                            self.control_barrier(self.exit_barrier_pin, "open", self.exit_led_pin)
                            self.exit_barrier_open = True
                            
                            # Create exit session
                            self.create_exit_session(plate_text)
                            
                            # Trigger buzzer
                            self.trigger_buzzer(2)
                            
                            # Close barrier after delay
                            threading.Timer(self.barrier_open_time, self.close_exit_barrier).start()
                            
                            last_detection_time = current_time
                            break
                        else:
                            print(f"❌ Vehicle {plate_text} not in permanent parking")
                            # Trigger buzzer for unauthorized vehicle
                            self.trigger_buzzer(1)
            
            # Display frame (optional)
            cv2.imshow('Exit Camera - ANPR System', frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        
        cap.release()
        cv2.destroyAllWindows()
        print("📹 Exit camera processing stopped")
    
    def close_entry_barrier(self):
        """Close entry barrier"""
        self.control_barrier(self.entry_barrier_pin, "close", self.entry_led_pin)
        self.entry_barrier_open = False
        print("🚧 Entry barrier closed")
    
    def close_exit_barrier(self):
        """Close exit barrier"""
        self.control_barrier(self.exit_barrier_pin, "close", self.exit_led_pin)
        self.exit_barrier_open = False
        print("🚧 Exit barrier closed")
    
    def start_system(self):
        """Start the ANPR system"""
        print("🚀 Starting ANPR Trigger System...")
        print("=" * 60)
        
        self.running = True
        
        # Start entry camera thread
        self.entry_thread = threading.Thread(target=self.process_entry_camera)
        self.entry_thread.daemon = True
        self.entry_thread.start()
        
        # Start exit camera thread
        self.exit_thread = threading.Thread(target=self.process_exit_camera)
        self.exit_thread.daemon = True
        self.exit_thread.start()
        
        print("✅ ANPR System started")
        print("   Entry camera: Active")
        print("   Exit camera: Active")
        print("   Press Ctrl+C to stop")
        
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            self.stop_system()
    
    def stop_system(self):
        """Stop the ANPR system"""
        print("\n🛑 Stopping ANPR System...")
        self.running = False
        
        # Close barriers
        self.close_entry_barrier()
        self.close_exit_barrier()
        
        # Wait for threads to finish
        if self.entry_thread:
            self.entry_thread.join(timeout=5)
        if self.exit_thread:
            self.exit_thread.join(timeout=5)
        
        print("✅ ANPR System stopped")

def main():
    print("🚗 ANPR Trigger System - Entry/Exit Control")
    print("=" * 60)
    print("This system handles:")
    print("• Entry camera detection")
    print("• Exit camera detection")
    print("• Database checking")
    print("• Boom barrier control")
    print("• Session management")
    print("=" * 60)
    
    # Create system
    anpr_system = ANPRTriggerSystem()
    
    # Start system
    anpr_system.start_system()

if __name__ == "__main__":
    main()

