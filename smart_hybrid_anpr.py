#!/usr/bin/env python3
"""
Smart Hybrid ANPR System
Uses OpenCV for initial detection, Plate Recognizer API for accurate OCR
Only sends to API when potential plate is detected
"""

import cv2
import numpy as np
import requests
import base64
import time
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class SmartHybridANPR:
    def __init__(self, api_key=None):
        """
        Initialize Smart Hybrid ANPR System
        
        Args:
            api_key: Plate Recognizer API key (optional)
        """
        self.api_key = api_key
        self.api_available = bool(api_key and api_key != "YOUR_API_KEY_HERE")
        
        # Detection settings
        self.detection_interval = 2.0  # Check every 2 seconds
        self.last_detection_time = 0
        self.min_plate_area = 1000
        self.max_plate_area = 100000
        self.min_aspect_ratio = 1.5
        self.max_aspect_ratio = 5.0
        
        # API settings
        self.api_base_url = "https://api.platerecognizer.com/v1/plate-reader/"
        self.api_headers = {
            "Authorization": f"Token {self.api_key}"
        } if self.api_available else {}
        
        # Detection history to avoid duplicates
        self.recent_detections = []
        self.detection_cooldown = 10  # seconds
        
        logger.info(f"🔧 Smart Hybrid ANPR initialized - API: {'✅ Available' if self.api_available else '❌ Not available'}")
    
    def detect_potential_plates_opencv(self, image):
        """
        Use OpenCV to detect potential plate regions (fast, local)
        Only returns regions that look like number plates
        """
        try:
            # Convert to grayscale
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Apply CLAHE for better contrast
            clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
            enhanced = clahe.apply(gray)
            
            # Apply bilateral filter
            filtered = cv2.bilateralFilter(enhanced, 11, 17, 17)
            
            # Apply Gaussian blur
            blurred = cv2.GaussianBlur(filtered, (5, 5), 0)
            
            # Apply sharpening
            kernel = np.array([[-1, -1, -1], [-1, 9, -1], [-1, -1, -1]])
            sharpened = cv2.filter2D(blurred, -1, kernel)
            
            # Multiple edge detection
            edges1 = cv2.Canny(sharpened, 50, 150)
            edges2 = cv2.Canny(sharpened, 100, 200)
            edges3 = cv2.Canny(sharpened, 30, 100)
            
            # Combine edges
            combined_edges = cv2.bitwise_or(edges1, edges2)
            combined_edges = cv2.bitwise_or(combined_edges, edges3)
            
            # Morphological operations
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
            morphed = cv2.morphologyEx(combined_edges, cv2.MORPH_CLOSE, kernel)
            
            # Find contours
            contours, _ = cv2.findContours(morphed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            potential_plates = []
            
            for contour in contours:
                area = cv2.contourArea(contour)
                
                # Filter by area
                if self.min_plate_area < area < self.max_plate_area:
                    x, y, w, h = cv2.boundingRect(contour)
                    aspect_ratio = w / h
                    
                    # Filter by aspect ratio
                    if self.min_aspect_ratio <= aspect_ratio <= self.max_aspect_ratio:
                        # Calculate quality metrics
                        hull = cv2.convexHull(contour)
                        hull_area = cv2.contourArea(hull)
                        solidity = area / hull_area if hull_area > 0 else 0
                        
                        rect_area = w * h
                        extent = area / rect_area if rect_area > 0 else 0
                        
                        # Quality filter
                        if solidity > 0.3 and extent > 0.2:
                            potential_plates.append({
                                'bbox': (x, y, w, h),
                                'area': area,
                                'aspect_ratio': aspect_ratio,
                                'solidity': solidity,
                                'extent': extent,
                                'contour': contour
                            })
            
            # Sort by quality (area * solidity * extent)
            potential_plates.sort(key=lambda x: x['area'] * x['solidity'] * x['extent'], reverse=True)
            
            # Return top 3 candidates
            return potential_plates[:3]
            
        except Exception as e:
            logger.error(f"OpenCV detection error: {e}")
            return []
    
    def send_to_api(self, image, region):
        """
        Send image region to Plate Recognizer API
        Only called when potential plate is detected
        """
        if not self.api_available:
            logger.warning("⚠️ API not available - using fallback")
            return self.fallback_ocr(image, region)
        
        try:
            x, y, w, h = region['bbox']
            
            # Extract region from image
            plate_region = image[y:y+h, x:x+w]
            
            # Convert to base64
            _, buffer = cv2.imencode('.jpg', plate_region)
            image_base64 = base64.b64encode(buffer).decode('utf-8')
            
            # Prepare request
            data = {
                'image': image_base64,
                'regions': ['in'],  # Focus on Indian plates
                'config': '{"region": {"type": "polygon", "vertices": [[0, 0], [image_width, 0], [image_width, image_height], [0, image_height]]}}'
            }
            
            # Make API request
            response = requests.post(
                self.api_base_url,
                headers=self.api_headers,
                data=data,
                timeout=5
            )
            
            if response.status_code == 200:
                result = response.json()
                plates = []
                
                for detection in result.get('results', []):
                    plate_text = detection.get('plate', '').upper().strip()
                    confidence = detection.get('score', 0.0)
                    
                    if plate_text and len(plate_text) >= 4:
                        plates.append({
                            'text': plate_text,
                            'confidence': confidence,
                            'timestamp': datetime.now(),
                            'bbox': region['bbox'],
                            'source': 'api'
                        })
                
                logger.info(f"🔍 API detected {len(plates)} plates")
                return plates
            else:
                logger.error(f"❌ API request failed: {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"❌ API error: {e}")
            return []
    
    def fallback_ocr(self, image, region):
        """
        Fallback OCR when API is not available
        Uses basic text detection
        """
        try:
            x, y, w, h = region['bbox']
            plate_region = image[y:y+h, x:x+w]
            
            # Simple text detection (placeholder)
            # In real implementation, you'd use Tesseract or EasyOCR
            return [{
                'text': f"PLATE_{int(time.time())}",  # Placeholder
                'confidence': 0.5,
                'timestamp': datetime.now(),
                'bbox': region['bbox'],
                'source': 'fallback'
            }]
            
        except Exception as e:
            logger.error(f"Fallback OCR error: {e}")
            return []
    
    def is_duplicate_detection(self, plate_text, bbox):
        """
        Check if this is a duplicate detection
        Prevents sending same plate to API multiple times
        """
        current_time = time.time()
        
        # Clean up old detections
        self.recent_detections = [
            d for d in self.recent_detections 
            if current_time - d['timestamp'] < self.detection_cooldown
        ]
        
        # Check for duplicates
        for detection in self.recent_detections:
            if (detection['text'] == plate_text and 
                abs(detection['bbox'][0] - bbox[0]) < 50 and
                abs(detection['bbox'][1] - bbox[1]) < 50):
                return True
        
        return False
    
    def detect_license_plates(self, image):
        """
        Main detection function
        Uses OpenCV for initial detection, API for accurate OCR
        """
        current_time = time.time()
        
        # Only check every detection_interval seconds
        if current_time - self.last_detection_time < self.detection_interval:
            return [], image
        
        self.last_detection_time = current_time
        
        try:
            # Step 1: Use OpenCV to find potential plate regions
            potential_plates = self.detect_potential_plates_opencv(image)
            
            if not potential_plates:
                logger.debug("🔍 No potential plates detected")
                return [], image
            
            logger.info(f"🔍 Found {len(potential_plates)} potential plates")
            
            detected_plates = []
            
            for region in potential_plates:
                x, y, w, h = region['bbox']
                
                # Draw rectangle around potential plate
                cv2.rectangle(image, (x, y), (x + w, y + h), (0, 255, 0), 2)
                cv2.putText(image, "Potential Plate", (x, y - 10), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                
                # Step 2: Send to API for accurate OCR
                api_results = self.send_to_api(image, region)
                
                for plate in api_results:
                    # Check for duplicates
                    if not self.is_duplicate_detection(plate['text'], plate['bbox']):
                        detected_plates.append(plate)
                        
                        # Add to recent detections
                        self.recent_detections.append({
                            'text': plate['text'],
                            'bbox': plate['bbox'],
                            'timestamp': current_time
                        })
                        
                        # Draw final result
                        cv2.putText(image, plate['text'], (x, y - 30), 
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                        cv2.putText(image, f"Conf: {plate['confidence']:.2f}", (x, y - 50), 
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
                        
                        logger.info(f"✅ Plate detected: {plate['text']} (confidence: {plate['confidence']:.2f})")
            
            return detected_plates, image
            
        except Exception as e:
            logger.error(f"Detection error: {e}")
            return [], image
    
    def get_api_usage_stats(self):
        """Get API usage statistics"""
        return {
            'api_available': self.api_available,
            'recent_detections': len(self.recent_detections),
            'detection_interval': self.detection_interval,
            'cooldown_period': self.detection_cooldown
        }

# Test function
def test_smart_hybrid_anpr():
    """Test the smart hybrid ANPR system"""
    print("🔍 Testing Smart Hybrid ANPR...")
    print("=" * 50)
    
    # Initialize without API key for testing
    anpr = SmartHybridANPR()
    
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("❌ Could not open camera")
        return
    
    print("✅ Camera opened")
    print("📋 Show a number plate to the camera")
    print("⏹️ Press 'q' to quit")
    print("=" * 50)
    
    frame_count = 0
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        frame_count += 1
        
        # Detect plates
        detected_plates, processed_frame = anpr.detect_license_plates(frame)
        
        if detected_plates:
            print(f"✅ Detected {len(detected_plates)} plates:")
            for plate in detected_plates:
                print(f"  - {plate['text']} (confidence: {plate['confidence']:.2f})")
        
        # Display frame
        cv2.imshow('Smart Hybrid ANPR', processed_frame)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    cap.release()
    cv2.destroyAllWindows()
    
    # Show stats
    stats = anpr.get_api_usage_stats()
    print(f"\n📊 API Usage Stats:")
    print(f"  API Available: {stats['api_available']}")
    print(f"  Recent Detections: {stats['recent_detections']}")
    print(f"  Detection Interval: {stats['detection_interval']}s")
    print(f"  Cooldown Period: {stats['cooldown_period']}s")

if __name__ == "__main__":
    test_smart_hybrid_anpr()

