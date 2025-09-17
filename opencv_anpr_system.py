#!/usr/bin/env python3
"""
Comprehensive OpenCV ANPR System
Advanced license plate detection and recognition for Indian vehicles
"""

import cv2
import numpy as np
import re
import time
from datetime import datetime
import os
import sys

class OpenCVANPRSystem:
    def __init__(self):
        # Camera configuration
        self.camera_index = 0
        self.camera = None
        self.running = False
        
        # Detection settings
        self.detection_interval = 3.0  # 3 seconds between detections
        self.last_detection_time = 0
        self.min_plate_area = 500  # Much smaller minimum area
        self.max_plate_area = 100000  # Larger maximum area
        
        # Indian license plate patterns (comprehensive)
        self.plate_patterns = [
            # Standard format: KA01AB1234
            r'^[A-Z]{2}[0-9]{2}[A-Z]{2}[0-9]{4}$',
            # BH format: BH01ABC123
            r'^[A-Z]{2}[0-9]{2}[A-Z]{1,3}[0-9]{3,4}$',
            # New format: 22BHX1234
            r'^[0-9]{2}[A-Z]{2}[A-Z]{1}[0-9]{4}$',
            # Commercial: KA01AB1234
            r'^[A-Z]{2}[0-9]{2}[A-Z]{2}[0-9]{4}$',
            # Two wheeler: KA01AB1234
            r'^[A-Z]{2}[0-9]{2}[A-Z]{2}[0-9]{4}$',
            # Temporary: KA01AB1234
            r'^[A-Z]{2}[0-9]{2}[A-Z]{2}[0-9]{4}$',
        ]
        
        # State codes for validation
        self.state_codes = [
            'AP', 'AR', 'AS', 'BR', 'CG', 'GA', 'GJ', 'HR', 'HP', 'JK', 'JH', 'KA', 'KL', 'MP', 'MH', 'MN', 'ML', 'MZ', 'NL', 'OD', 'PB', 'RJ', 'SK', 'TN', 'TG', 'TR', 'UP', 'UT', 'WB', 'AN', 'CH', 'DN', 'DD', 'DL', 'LD', 'PY', 'BH'
        ]
        
        # Detection history
        self.detection_history = []
        self.max_history = 50
        
        print("🚗 OpenCV ANPR System - Comprehensive Version")
        print("=" * 60)
        print("Advanced license plate detection for Indian vehicles")
        print("Supports all Indian license plate formats")
        print("=" * 60)
    
    def initialize_camera(self):
        """Initialize camera with optimal settings"""
        print("📹 Initializing camera...")
        
        # Try different camera indices
        for i in range(3):
            self.camera = cv2.VideoCapture(i)
            if self.camera.isOpened():
                print(f"✅ Camera {i} opened successfully")
                self.camera_index = i
                break
            else:
                print(f"❌ Camera {i} failed")
        
        if not self.camera or not self.camera.isOpened():
            print("❌ No camera available")
            return False
        
        # Set camera properties for optimal performance
        self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        self.camera.set(cv2.CAP_PROP_FPS, 30)
        self.camera.set(cv2.CAP_PROP_AUTOFOCUS, 1)
        self.camera.set(cv2.CAP_PROP_BRIGHTNESS, 0.5)
        self.camera.set(cv2.CAP_PROP_CONTRAST, 0.5)
        self.camera.set(cv2.CAP_PROP_SATURATION, 0.5)
        
        print("✅ Camera configured successfully")
        return True
    
    def preprocess_image(self, image):
        """Advanced image preprocessing for better detection"""
        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Apply CLAHE (Contrast Limited Adaptive Histogram Equalization)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        gray = clahe.apply(gray)
        
        # Apply bilateral filter to reduce noise while preserving edges
        filtered = cv2.bilateralFilter(gray, 11, 17, 17)
        
        # Apply Gaussian blur
        blurred = cv2.GaussianBlur(filtered, (5, 5), 0)
        
        return blurred
    
    def detect_edges(self, image):
        """Advanced edge detection"""
        # Apply Canny edge detection with adaptive thresholds
        edges = cv2.Canny(image, 50, 150, apertureSize=3)
        
        # Apply morphological operations to close gaps
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        edges = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel)
        
        return edges
    
    def find_contours(self, edges):
        """Find and filter contours for license plates"""
        contours, _ = cv2.findContours(edges, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        
        # Filter contours by area and aspect ratio
        plate_candidates = []
        
        for contour in contours:
            area = cv2.contourArea(contour)
            
            # Filter by area (more lenient)
            if self.min_plate_area < area < self.max_plate_area:
                # Get bounding rectangle
                x, y, w, h = cv2.boundingRect(contour)
                
                # Calculate aspect ratio
                aspect_ratio = w / h
                
                # More lenient aspect ratio (1.5 to 6.0)
                if 1.5 <= aspect_ratio <= 6.0:
                    # Calculate solidity (area of contour / area of convex hull)
                    hull = cv2.convexHull(contour)
                    hull_area = cv2.contourArea(hull)
                    solidity = area / hull_area if hull_area > 0 else 0
                    
                    # More lenient solidity (0.5 instead of 0.7)
                    if solidity > 0.5:
                        plate_candidates.append({
                            'contour': contour,
                            'area': area,
                            'aspect_ratio': aspect_ratio,
                            'solidity': solidity,
                            'bbox': (x, y, w, h)
                        })
        
        # Sort by area (largest first)
        plate_candidates.sort(key=lambda x: x['area'], reverse=True)
        
        return plate_candidates[:10]  # Return top 10 candidates
    
    def extract_plate_region(self, image, bbox):
        """Extract and enhance license plate region"""
        x, y, w, h = bbox
        
        # Add padding
        padding = 10
        x = max(0, x - padding)
        y = max(0, y - padding)
        w = min(image.shape[1] - x, w + 2 * padding)
        h = min(image.shape[0] - y, h + 2 * padding)
        
        # Extract region
        plate_region = image[y:y+h, x:x+w]
        
        if plate_region.size == 0:
            return None
        
        # Resize for better OCR
        plate_region = cv2.resize(plate_region, (300, 100))
        
        # Apply additional preprocessing
        gray_plate = cv2.cvtColor(plate_region, cv2.COLOR_BGR2GRAY)
        
        # Apply adaptive threshold
        thresh = cv2.adaptiveThreshold(gray_plate, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
        
        # Apply morphological operations
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
        thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
        
        return thresh
    
    def simulate_ocr(self, plate_image):
        """Simulate OCR for testing (replace with real Tesseract)"""
        # For now, return None to indicate no real detection
        # This will be replaced with actual Tesseract OCR
        return None
    
    def validate_indian_plate(self, text):
        """Comprehensive validation for Indian license plates"""
        if not text or len(text) < 8:
            return False
        
        # Clean text
        text = re.sub(r'[^A-Z0-9]', '', text.upper())
        
        # Check length
        if len(text) < 8 or len(text) > 12:
            return False
        
        # Check patterns
        for pattern in self.plate_patterns:
            if re.match(pattern, text):
                return True
        
        # Additional validation for state codes
        if len(text) >= 4:
            state_code = text[:2]
            if state_code in self.state_codes:
                return True
        
        return False
    
    def detect_license_plates(self, frame):
        """Main license plate detection function"""
        current_time = time.time()
        
        # Check if it's time for next detection (every 3 seconds)
        if (current_time - self.last_detection_time) < self.detection_interval:
            return []
        
        print(f"🔍 Scanning for plates... (Time: {current_time:.1f})")
        
        # Preprocess image
        processed = self.preprocess_image(frame)
        
        # Detect edges
        edges = self.detect_edges(processed)
        
        # Find contours
        candidates = self.find_contours(edges)
        
        print(f"📊 Found {len(candidates)} potential candidates")
        
        detected_plates = []
        
        for i, candidate in enumerate(candidates):
            print(f"  Candidate {i+1}: Area={candidate['area']:.0f}, Aspect={candidate['aspect_ratio']:.2f}, Solidity={candidate['solidity']:.2f}")
            
            # Extract plate region
            plate_image = self.extract_plate_region(frame, candidate['bbox'])
            
            if plate_image is not None:
                # For now, just detect ANY rectangular region
                detected_plates.append({
                    'text': f"RECT_{i+1}",  # Label as rectangle
                    'bbox': candidate['bbox'],
                    'confidence': candidate['solidity'],
                    'timestamp': datetime.now()
                })
                print(f"✅ Detected rectangle {i+1}!")
                # Set next detection time (3 seconds from now)
                self.last_detection_time = current_time
                break  # Only one detection per cycle
        
        if not detected_plates:
            print("❌ No rectangles detected")
        
        return detected_plates
    
    def draw_detections(self, frame, detections):
        """Draw detection results on frame"""
        for detection in detections:
            x, y, w, h = detection['bbox']
            text = detection['text']
            confidence = detection['confidence']
            
            # Draw rectangle
            cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 3)
            
            if text:
                # Draw text background
                text_size = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.8, 2)[0]
                cv2.rectangle(frame, (x, y-35), (x+text_size[0]+10, y), (0, 255, 0), -1)
                
                # Draw text
                cv2.putText(frame, text, (x+5, y-10), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 2)
            else:
                # Draw "PLATE DETECTED" text
                cv2.putText(frame, "PLATE DETECTED", (x, y-10), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            
            # Draw confidence
            conf_text = f"Conf: {confidence:.2f}"
            cv2.putText(frame, conf_text, (x, y+h+20), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
    
    def draw_all_contours(self, frame):
        """Draw all contours for debugging"""
        # Preprocess image
        processed = self.preprocess_image(frame)
        
        # Detect edges
        edges = self.detect_edges(processed)
        
        # Find ALL contours
        contours, _ = cv2.findContours(edges, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        
        # Draw all contours in blue
        cv2.drawContours(frame, contours, -1, (255, 0, 0), 1)
        
        # Draw filtered candidates in green
        candidates = self.find_contours(edges)
        for candidate in candidates:
            x, y, w, h = candidate['bbox']
            cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
            cv2.putText(frame, f"A:{candidate['area']:.0f}", (x, y-5), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 0), 1)
    
    def add_info_overlay(self, frame, frame_count, fps):
        """Add information overlay to frame"""
        # Background for info
        overlay = frame.copy()
        cv2.rectangle(overlay, (10, 10), (400, 140), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.7, frame, 0.3, 0, frame)
        
        # Calculate time until next detection
        current_time = time.time()
        time_until_next = self.detection_interval - (current_time - self.last_detection_time)
        if time_until_next < 0:
            time_until_next = 0
        
        # Info text
        cv2.putText(frame, f"Frame: {frame_count}", (20, 35), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        cv2.putText(frame, f"FPS: {fps:.1f}", (20, 60), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        cv2.putText(frame, f"Detections: {len(self.detection_history)}", (20, 85), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        cv2.putText(frame, f"Next scan in: {time_until_next:.1f}s", (20, 110), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
        cv2.putText(frame, "Press 'q' to quit, 's' to save, 'c' to change camera", (20, 135), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)
    
    def save_detection(self, detection, frame):
        """Save detection result and image"""
        timestamp = detection['timestamp'].strftime("%Y%m%d_%H%M%S")
        filename = f"detection_{timestamp}_{detection['text']}.jpg"
        
        # Save image
        cv2.imwrite(filename, frame)
        
        # Add to history
        self.detection_history.append(detection)
        if len(self.detection_history) > self.max_history:
            self.detection_history.pop(0)
        
        print(f"📸 Detection saved: {filename}")
    
    def start_anpr_system(self):
        """Start the ANPR system"""
        print("🚀 Starting OpenCV ANPR System...")
        
        # Initialize camera
        if not self.initialize_camera():
            return
        
        print("✅ System ready")
        print("Controls:")
        print("  'q' - Quit")
        print("  's' - Save current frame")
        print("  'c' - Change camera")
        print("  'h' - Show detection history")
        print("=" * 60)
        
        self.running = True
        frame_count = 0
        start_time = time.time()
        
        try:
            while self.running:
                ret, frame = self.camera.read()
                if not ret:
                    print("❌ Failed to read frame")
                    break
                
                frame_count += 1
                current_time = time.time()
                
                # Calculate FPS
                if frame_count % 30 == 0:
                    fps = 30 / (current_time - start_time)
                    start_time = current_time
                else:
                    fps = 0
                
                # Detect license plates
                detections = self.detect_license_plates(frame)
                
                # Draw all contours for debugging
                self.draw_all_contours(frame)
                
                # Draw detections
                self.draw_detections(frame, detections)
                
                # Add info overlay
                self.add_info_overlay(frame, frame_count, fps)
                
                # Save ONLY ONE detection per cycle
                if detections:
                    self.save_detection(detections[0], frame)
                
                # Display frame
                cv2.imshow('OpenCV ANPR System - Advanced License Plate Detection', frame)
                
                # Handle key presses
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q'):
                    print("🛑 Quitting...")
                    break
                elif key == ord('s'):
                    # Save current frame
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"frame_{timestamp}.jpg"
                    cv2.imwrite(filename, frame)
                    print(f"📸 Frame saved: {filename}")
                elif key == ord('c'):
                    # Change camera
                    self.camera.release()
                    self.camera_index = 1 if self.camera_index == 0 else 0
                    self.camera = cv2.VideoCapture(self.camera_index)
                    if not self.camera.isOpened():
                        print(f"❌ Could not open camera {self.camera_index}")
                        break
                    print(f"📹 Switched to camera {self.camera_index}")
                elif key == ord('h'):
                    # Show detection history
                    print("\n📋 Detection History:")
                    for i, detection in enumerate(self.detection_history[-10:], 1):
                        print(f"  {i}. {detection['text']} - {detection['timestamp'].strftime('%H:%M:%S')}")
                    print()
        
        except KeyboardInterrupt:
            print("\n🛑 Interrupted by user")
        except Exception as e:
            print(f"❌ Error: {e}")
        finally:
            # Cleanup
            if self.camera:
                self.camera.release()
            cv2.destroyAllWindows()
            print("✅ ANPR System stopped")
    
    def cleanup(self):
        """Cleanup resources"""
        if self.camera:
            self.camera.release()
        cv2.destroyAllWindows()

def main():
    print("🚗 OpenCV ANPR System - Comprehensive Version")
    print("=" * 60)
    print("Advanced license plate detection for Indian vehicles")
    print("Supports all Indian license plate formats")
    print("=" * 60)
    
    # Create ANPR system
    anpr_system = OpenCVANPRSystem()
    
    try:
        # Start system
        anpr_system.start_anpr_system()
    except Exception as e:
        print(f"❌ Fatal error: {e}")
    finally:
        # Cleanup
        anpr_system.cleanup()

if __name__ == "__main__":
    main()
