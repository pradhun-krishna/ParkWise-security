#!/usr/bin/env python3
# Simple ANPR Trigger System - Easy to test
# Handles camera triggers, plate detection, and database checking

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

class SimpleANPRTrigger:
    def __init__(self):
        # Camera configuration
        self.entry_camera = int(os.getenv('ENTRY_CAMERA_INDEX', 0))
        self.exit_camera = int(os.getenv('EXIT_CAMERA_INDEX', 1))
        
        # Detection settings
        self.detection_interval = 3  # seconds between detections
        self.barrier_open_time = 10  # seconds barrier stays open
        
        # System state
        self.running = False
        
        # Indian license plate patterns
        self.plate_patterns = [
            r'^[A-Z]{2}[0-9]{2}[A-Z]{2}[0-9]{4}$',  # KA01AB1234
            r'^[A-Z]{2}[0-9]{2}[A-Z]{1,3}[0-9]{3,4}$',  # BH01ABC123
        ]
        
        print("🚗 Simple ANPR Trigger System")
        print(f"   Entry Camera: {self.entry_camera}")
        print(f"   Exit Camera: {self.exit_camera}")
    
    def detect_plates(self, frame):
        """Detect license plates in frame"""
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
                
                # Check aspect ratio
                aspect_ratio = w / h
                if 2.0 <= aspect_ratio <= 5.0 and w > 100 and h > 30:
                    plate_region = frame[y:y+h, x:x+w]
                    plates.append({
                        'region': plate_region,
                        'coordinates': (x, y, w, h)
                    })
        
        return plates
    
    def simulate_ocr(self, plate_image):
        """Simulate OCR for testing"""
        # Simulate different plates for testing
        simulated_plates = [
            "KA01AB1234", "MH02CD5678", "DL04GH3456", "TN03EF9012",
            "BH01ABC123", "GJ05IJ789", "UP15AB1234", "RJ14CD5678"
        ]
        
        import random
        return random.choice(simulated_plates)
    
    def validate_plate(self, text):
        """Validate Indian license plate"""
        if not text or len(text) < 8:
            return False
        
        text = re.sub(r'[^A-Z0-9]', '', text.upper())
        
        for pattern in self.plate_patterns:
            if re.match(pattern, text):
                return True
        
        return False
    
    def check_database(self, plate_number):
        """Check if vehicle exists in database"""
        try:
            query = "SELECT vehicle_number FROM shobha_permanent_parking WHERE vehicle_number = %s"
            result = db.execute_query(query, (plate_number,), fetch_one=True)
            return result is not None
        except Exception as e:
            print(f"❌ Database error: {e}")
            return False
    
    def create_session(self, plate_number, session_type):
        """Create entry or exit session"""
        try:
            if session_type == "entry":
                print(f"📝 Creating entry session for {plate_number}")
                # In real implementation, create entry session
                return True
            elif session_type == "exit":
                print(f"📝 Creating exit session for {plate_number}")
                # In real implementation, create exit session
                return True
        except Exception as e:
            print(f"❌ Session error: {e}")
            return False
    
    def control_barrier(self, barrier_type, action):
        """Control boom barrier"""
        if action == "open":
            print(f"🚧 Opening {barrier_type} barrier")
            print(f"🟢 {barrier_type.upper()} LED - GREEN")
            return True
        elif action == "close":
            print(f"🚧 Closing {barrier_type} barrier")
            print(f"🔴 {barrier_type.upper()} LED - OFF")
            return True
        return False
    
    def process_camera(self, camera_index, camera_type):
        """Process camera feed"""
        print(f"📹 Starting {camera_type} camera processing...")
        
        cap = cv2.VideoCapture(camera_index)
        if not cap.isOpened():
            print(f"❌ Could not open {camera_type} camera {camera_index}")
            return
        
        frame_count = 0
        last_detection_time = 0
        
        while self.running:
            ret, frame = cap.read()
            if not ret:
                continue
            
            frame_count += 1
            current_time = time.time()
            
            # Process every 30th frame
            if frame_count % 30 == 0 and (current_time - last_detection_time) > self.detection_interval:
                plates = self.detect_plates(frame)
                
                for plate in plates:
                    # Simulate OCR
                    plate_text = self.simulate_ocr(plate['region'])
                    
                    if plate_text and self.validate_plate(plate_text):
                        print(f"🚗 {camera_type.upper()} detected: {plate_text}")
                        
                        # Check database
                        if self.check_database(plate_text):
                            print(f"✅ Vehicle {plate_text} found in database")
                            
                            # Open barrier
                            self.control_barrier(camera_type, "open")
                            
                            # Create session
                            self.create_session(plate_text, camera_type)
                            
                            # Close barrier after delay
                            threading.Timer(self.barrier_open_time, 
                                          lambda: self.control_barrier(camera_type, "close")).start()
                            
                            last_detection_time = current_time
                            break
                        else:
                            print(f"❌ Vehicle {plate_text} not in database")
            
            # Draw rectangles around detected plates
            plates = self.detect_plates(frame)
            for plate in plates:
                x, y, w, h = plate['coordinates']
                cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
                cv2.putText(frame, f"{camera_type.upper()}", (x, y-10), 
                          cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            
            # Display frame
            cv2.imshow(f'{camera_type.upper()} Camera - ANPR System', frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        
        cap.release()
        cv2.destroyAllWindows()
        print(f"📹 {camera_type} camera processing stopped")
    
    def start_system(self):
        """Start the ANPR system"""
        print("🚀 Starting Simple ANPR Trigger System...")
        print("=" * 60)
        
        self.running = True
        
        # Start entry camera thread
        entry_thread = threading.Thread(target=self.process_camera, 
                                      args=(self.entry_camera, "entry"))
        entry_thread.daemon = True
        entry_thread.start()
        
        # Start exit camera thread
        exit_thread = threading.Thread(target=self.process_camera, 
                                     args=(self.exit_camera, "exit"))
        exit_thread.daemon = True
        exit_thread.start()
        
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
        print("✅ ANPR System stopped")

def main():
    print("🚗 Simple ANPR Trigger System")
    print("=" * 60)
    print("This system handles:")
    print("• Entry camera detection")
    print("• Exit camera detection")
    print("• Database checking")
    print("• Boom barrier control")
    print("• Session management")
    print("=" * 60)
    
    # Create system
    anpr_system = SimpleANPRTrigger()
    
    # Start system
    anpr_system.start_system()

if __name__ == "__main__":
    main()

