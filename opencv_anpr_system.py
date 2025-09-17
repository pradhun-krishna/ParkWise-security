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
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(gray)
        
        # Apply bilateral filter to reduce noise while preserving edges
        filtered = cv2.bilateralFilter(enhanced, 11, 17, 17)
        
        # Apply Gaussian blur
        blurred = cv2.GaussianBlur(filtered, (5, 5), 0)
        
        # Apply sharpening
        kernel = np.array([[-1,-1,-1], [-1,9,-1], [-1,-1,-1]])
        sharpened = cv2.filter2D(blurred, -1, kernel)
        
        return sharpened
    
    def detect_edges(self, image):
        """Advanced edge detection with multiple methods"""
        # Method 1: Canny with different thresholds
        edges1 = cv2.Canny(image, 30, 100)
        edges2 = cv2.Canny(image, 50, 150)
        edges3 = cv2.Canny(image, 100, 200)
        
        # Combine different Canny results
        combined_canny = cv2.bitwise_or(edges1, edges2)
        combined_canny = cv2.bitwise_or(combined_canny, edges3)
        
        # Method 2: Sobel edge detection
        sobelx = cv2.Sobel(image, cv2.CV_64F, 1, 0, ksize=3)
        sobely = cv2.Sobel(image, cv2.CV_64F, 0, 1, ksize=3)
        sobel_edges = np.sqrt(sobelx**2 + sobely**2)
        sobel_edges = np.uint8(sobel_edges / sobel_edges.max() * 255)
        
        # Combine all methods
        final_edges = cv2.bitwise_or(combined_canny, sobel_edges)
        
        # Apply morphological operations to connect broken edges
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        final_edges = cv2.morphologyEx(final_edges, cv2.MORPH_CLOSE, kernel)
        
        return final_edges
    
    def find_contours(self, edges):
        """Find and filter contours for license plates with strict criteria"""
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        plate_candidates = []
        
        for contour in contours:
            area = cv2.contourArea(contour)
            
            # Filter by area (license plates are typically 1000-50000 pixels)
            if area < 1000 or area > 50000:
                continue
                
            # Get bounding rectangle
            x, y, w, h = cv2.boundingRect(contour)
            aspect_ratio = w / h
            
            # License plates typically have aspect ratio between 2.0 and 4.0
            if not (2.0 <= aspect_ratio <= 4.0):
                continue
                
            # Check if contour is roughly rectangular
            hull = cv2.convexHull(contour)
            hull_area = cv2.contourArea(hull)
            solidity = area / hull_area if hull_area > 0 else 0
            
            # Should be fairly solid (rectangular)
            if solidity < 0.8:
                continue
                
            # Check extent (how much of the bounding rectangle is filled)
            extent = area / (w * h)
            if extent < 0.6:
                continue
                
            # Check if the contour is not too elongated
            if w < 50 or h < 15:
                continue
                
            plate_candidates.append({
                'contour': contour,
                'area': area,
                'aspect_ratio': aspect_ratio,
                'solidity': solidity,
                'extent': extent,
                'bbox': (x, y, w, h)
            })
        
        # Sort by area (largest first)
        plate_candidates.sort(key=lambda x: x['area'], reverse=True)
        
        return plate_candidates[:5]  # Return top 5 candidates
    
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
    
    def extract_text_ocr(self, plate_image):
        """Extract text using Tesseract OCR with multiple methods"""
        try:
            import pytesseract
            
            # Configure Tesseract for better number plate recognition
            configs = [
                '--oem 3 --psm 8 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ',
                '--oem 3 --psm 7 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ',
                '--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ',
                '--oem 3 --psm 13 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ'
            ]
            
            texts = []
            for config in configs:
                try:
                    text = pytesseract.image_to_string(plate_image, config=config)
                    if text and text.strip():
                        texts.append(text.strip().upper())
                except:
                    continue
            
            # Clean and validate texts
            valid_texts = []
            for text in texts:
                # Clean text (remove non-alphanumeric characters)
                cleaned = re.sub(r'[^A-Z0-9]', '', text)
                
                # Check if it looks like a license plate
                if self.validate_indian_plate(cleaned):
                    valid_texts.append(cleaned)
            
            # Return the most common valid text
            if valid_texts:
                return max(set(valid_texts), key=valid_texts.count)
                
        except ImportError:
            print("⚠️ Tesseract not available, using simulation")
        except Exception as e:
            print(f"⚠️ OCR error: {e}")
            
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
    
    def calculate_confidence(self, plate_text, candidate):
        """Calculate confidence score for detected plate"""
        base_confidence = 0.5
        
        # Add confidence for valid format
        if self.validate_indian_plate(plate_text):
            base_confidence += 0.3
            
        # Add confidence for reasonable length
        if 8 <= len(plate_text) <= 12:
            base_confidence += 0.2
            
        # Add confidence for character distribution
        if len(plate_text) >= 8:
            # Check if it has the right mix of letters and numbers
            letters = sum(1 for c in plate_text if c.isalpha())
            numbers = sum(1 for c in plate_text if c.isdigit())
            
            if letters >= 4 and numbers >= 4:
                base_confidence += 0.1
                
        # Add confidence based on contour quality
        base_confidence += candidate['solidity'] * 0.1
        base_confidence += candidate['extent'] * 0.1
                
        return min(1.0, base_confidence)
    
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
                # Try to extract text using OCR
                plate_text = self.extract_text_ocr(plate_image)
                
                if plate_text:
                    # Calculate confidence based on multiple factors
                    confidence = self.calculate_confidence(plate_text, candidate)
                    
                    detected_plates.append({
                        'text': plate_text,
                        'bbox': candidate['bbox'],
                        'confidence': confidence,
                        'timestamp': datetime.now()
                    })
                    print(f"✅ Detected plate: {plate_text} (Confidence: {confidence:.2f})")
                    # Set next detection time (3 seconds from now)
                    self.last_detection_time = current_time
                    break  # Only one detection per cycle
                else:
                    print(f"❌ No valid text found in candidate {i+1}")
        
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
